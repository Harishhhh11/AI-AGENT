import json

import pytest

from app.services.semantic_conversation_service import SemanticConversationService


class FakeLLM:
    def __init__(self, payload):
        self.payload = payload

    async def generate_structured(self, prompt):
        return json.dumps(self.payload)


@pytest.mark.asyncio
async def test_semantic_analysis_normalizes_intent_and_subject():
    service = SemanticConversationService(
        FakeLLM(
            {
                "intent": "fee",
                "subject": "Java Programming",
                "questions": [
                    {"text": "Whats the fee for java?", "intent": "fee", "subject": "Java Programming"}
                ],
                "response_style": "short",
                "requires_knowledge": True,
                "wants_lead_action": False,
            }
        )
    )
    result = await service.analyze(
        message="Whats the fee for java?",
        conversation_context="",
        available_subjects=["Java Programming"],
    )
    assert result is not None
    assert result.intent == "fee"
    assert result.subject == "Java Programming"


def test_fallback_detects_python_duration_after_paraphrase():
    service = SemanticConversationService(None)
    result = service.fallback("What is the duration for Python?", "")
    assert result.intent == "duration"
    assert result.subject == "python"


def test_fallback_splits_multi_question_message():
    service = SemanticConversationService(None)
    result = service.fallback("What is the fee for Java? What's the batch timings for Python?", "")
    assert len(result.questions) == 2
    assert result.questions[0]["intent"] == "fee"
    assert result.questions[1]["intent"] == "timings"
