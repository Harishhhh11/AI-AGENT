import pytest

from app.services.semantic_conversation_service import SemanticConversationService


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("Can I join online?", "mode"),
        ("can I attend remotely", "mode"),
        ("Do you have online classes", "mode"),
        ("What topics are covered?", "topics"),
        ("whats the fee?", "fee"),
        ("how long is it?", "duration"),
        ("batch timings please", "timings"),
    ],
)
def test_high_confidence_intent_handles_natural_variants(message, expected):
    service = SemanticConversationService(None)
    result = service.fallback(message, available_subjects=["Python Programming"])
    assert result.intent == expected
    assert result.requires_knowledge is True
    assert result.subject == "Python Programming"
