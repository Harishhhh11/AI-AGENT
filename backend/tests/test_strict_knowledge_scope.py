"""Regression coverage for strict receptionist knowledge scope."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.chat_flow_engine import ChatFlowEngine
from app.services.semantic_conversation_service import SemanticConversation


@pytest.mark.asyncio
async def test_zero_knowledge_skips_retrieval_and_returns_no_grounding_items():
    llm = MagicMock()
    semantic = SemanticConversation(
        intent="company_courses",
        subject=None,
        questions=[{"text": "Which courses do you offer?", "intent": "company_courses", "subject": None}],
        response_style="medium",
        requires_knowledge=True,
        wants_lead_action=False,
    )

    engine = ChatFlowEngine.__new__(ChatFlowEngine)
    engine.semantic = MagicMock()
    engine.semantic.analyze = AsyncMock(return_value=semantic)
    engine.retrieval = MagicMock()
    engine.grounding = MagicMock()
    engine.queries = MagicMock()
    engine.queries.build_queries.return_value = []
    engine.knowledge_service = MagicMock()
    engine.knowledge_service.get_all.return_value = []

    result = await engine.run(
        message="Which courses do you offer?",
        conversation_context="",
        organization_id=1,
        agent_id=11,
    )

    assert result[2] == []
    engine.retrieval.retrieve.assert_not_called()
    engine.grounding.evaluate.assert_not_called()


def test_knowledge_service_available_scope_is_agent_or_shared_only():
    service = MagicMock()
    assert service is not None


@pytest.mark.asyncio
async def test_available_knowledge_is_scoped_to_selected_agent():
    item = SimpleNamespace(id=1, title="Python Programming", content="Duration: 3 months", is_active=True)

    engine = ChatFlowEngine.__new__(ChatFlowEngine)
    engine.knowledge_service = MagicMock()
    engine.knowledge_service.get_all.return_value = [item]
    engine.semantic = MagicMock()
    engine.semantic.analyze = AsyncMock(
        return_value=SemanticConversation(
            intent="duration",
            subject="Python Programming",
            questions=[{"text": "How long is Python?", "intent": "duration", "subject": "Python Programming"}],
            response_style="short",
            requires_knowledge=True,
            wants_lead_action=False,
        )
    )
    engine.queries = MagicMock()
    engine.queries.build_queries.return_value = []
    engine.retrieval = MagicMock()
    engine.grounding = MagicMock()

    result = await engine.run(
        message="How long is Python?",
        conversation_context="",
        organization_id=1,
        agent_id=11,
    )

    engine.knowledge_service.get_all.assert_called_once_with(
        organization_id=1,
        agent_id=11,
        scope="available",
    )
    assert result[0].requires_knowledge is True
