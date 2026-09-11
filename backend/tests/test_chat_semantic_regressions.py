from types import SimpleNamespace

import pytest

from app.services.knowledge_answer_service import KnowledgeAnswerService
from app.services.semantic_conversation_service import SemanticConversationService


class FakeLLM:
    def __init__(self, payload):
        self.payload = payload

    async def generate_structured(self, prompt):
        import json
        return json.dumps(self.payload)


def test_semantic_service_handles_typo_and_subject():
    service = SemanticConversationService(FakeLLM({
        "intent": "certificate",
        "subject": "Java Programming",
        "questions": [{"text": "do you provide course complition certificate?", "intent": "certificate", "subject": "Java Programming"}],
        "response_style": "short",
        "requires_knowledge": True,
        "wants_lead_action": False,
    }))
    result = pytest.run(async_fn=service.analyze, message="do you provide course complition certificate?", conversation_context="", available_subjects=["Java Programming"])
    assert result.intent == "certificate"
    assert result.subject == "Java Programming"


def test_fallback_multi_question_keeps_each_subject():
    service = SemanticConversationService(None)
    result = service.fallback("What is the fee for Java? What's the batch timings for Python?")
    assert len(result.questions) == 2
    assert result.questions[0]["intent"] == "fee"
    assert result.questions[1]["intent"] == "timings"
    assert result.questions[0]["subject"] == "java"
    assert result.questions[1]["subject"] == "python"


def test_fact_answer_is_concise_and_not_source_dump():
    item = SimpleNamespace(title="JAVA PROGRAMMING COURSE", content="Course Fee: INR 25,000. Topics include Java, OOP and JDBC.")
    answer = KnowledgeAnswerService().answer(items=[item], intent="fee", subject="java", response_style="short")
    assert answer == "JAVA PROGRAMMING COURSE: Course Fee: INR 25,000."
    assert "Topics include" not in answer


def test_topics_answer_does_not_repeat_full_document():
    item = SimpleNamespace(
        title="JAVA PROGRAMMING COURSE",
        content="Course Name: Java Programming. Course Category: Programming. The course covers fundamentals. Topics: Variables, OOP, Inheritance, JDBC. Course Fee: INR 25,000.",
    )
    answer = KnowledgeAnswerService().answer(items=[item], intent="topics", subject="java", response_style="medium")
    assert "Variables" in answer
    assert "Inheritance" in answer
    assert "Course Fee" not in answer
    assert answer.count("JAVA PROGRAMMING COURSE") <= 1
