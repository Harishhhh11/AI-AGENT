from types import SimpleNamespace

import pytest

from app.services.chat_flow_engine import ChatFlowEngine


class FakeKnowledge:
    def __init__(self, items):
        self.items = items

    def get_all(self, **kwargs):
        return self.items


class FakeRetrieval:
    def __init__(self, results=None):
        self.results = results or []
        self.calls = []

    def retrieve(self, **kwargs):
        self.calls.append(kwargs)
        return self.results


class FakeGrounding:
    def evaluate(self, **kwargs):
        return SimpleNamespace(accepted=False)


class FakeAnswer:
    pass


@pytest.mark.asyncio
async def test_chat_flow_falls_back_to_single_scoped_knowledge_for_natural_fact_query():
    item = SimpleNamespace(id=1, title="Python Programming", content="Fee: INR 25,000. Classes are available online.", is_active=True)
    retrieval = FakeRetrieval()
    engine = ChatFlowEngine(
        llm=None,
        retrieval_service=retrieval,
        grounding_service=FakeGrounding(),
        answer_orchestrator=FakeAnswer(),
        knowledge_service=FakeKnowledge([item]),
    )

    semantic, queries, knowledge = await engine.run(
        message="What are the fees?",
        conversation_context="",
        organization_id=1,
        agent_id=2,
    )

    assert semantic.intent == "fee"
    assert semantic.subject == "Python Programming"
    assert queries[0]["subject"] == "Python Programming"
    assert knowledge == [item]
    assert retrieval.calls


@pytest.mark.asyncio
async def test_chat_flow_does_not_mix_unresolved_multiple_subjects():
    java = SimpleNamespace(id=1, title="Java Programming", content="Fee: INR 25,000.", is_active=True)
    python = SimpleNamespace(id=2, title="Python Programming", content="Fee: INR 30,000.", is_active=True)
    engine = ChatFlowEngine(
        llm=None,
        retrieval_service=FakeRetrieval(),
        grounding_service=FakeGrounding(),
        answer_orchestrator=FakeAnswer(),
        knowledge_service=FakeKnowledge([java, python]),
    )

    _, _, knowledge = await engine.run(
        message="What are the fees?",
        conversation_context="",
        organization_id=1,
        agent_id=2,
    )

    assert knowledge == []
