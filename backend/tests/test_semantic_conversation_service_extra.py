from app.services.semantic_conversation_service import SemanticConversationService


def test_fallback_handles_whats_typo_and_canonicalizes_subject():
    service = SemanticConversationService(None)
    result = service.fallback("Whats the fee?", available_subjects=["Java Programming"], conversation_context="")
    assert result.questions[0]["intent"] == "fee"
    assert result.questions[0]["subject"] == "Java Programming"


def test_fallback_handles_completion_typo_and_certificate_intent():
    service = SemanticConversationService(None)
    result = service.fallback(
        "do you provide course complition certificate?",
        available_subjects=["Java Programming"],
        conversation_context="",
    )
    assert result.questions[0]["intent"] == "certificate"


def test_fallback_handles_mixed_java_python_questions():
    service = SemanticConversationService(None)
    result = service.fallback(
        "What is the fee for java? what's the batch timings for python?",
        available_subjects=["Java Programming", "Python Programming"],
        conversation_context="",
    )
    assert len(result.questions) == 2
    assert result.questions[0]["subject"] == "Java Programming"
    assert result.questions[1]["subject"] == "Python Programming"
