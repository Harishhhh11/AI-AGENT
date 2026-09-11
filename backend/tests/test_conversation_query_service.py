from app.services.conversation_query_service import ConversationQueryService
from app.services.semantic_conversation_service import SemanticConversation


def test_query_builder_keeps_subject_and_intent_terms():
    service = ConversationQueryService()
    semantic = SemanticConversation(
        intent="fee",
        subject="Java Programming",
        questions=[{"text": "Whats the fee?", "intent": "fee", "subject": "Java Programming"}],
        response_style="short",
        requires_knowledge=True,
        wants_lead_action=False,
    )
    queries = service.build_queries(semantic=semantic, fallback_subject=None, original_message="Whats the fee?")
    assert len(queries) == 1
    assert "Java Programming" in queries[0]["query"]
    assert "price" in queries[0]["query"]


def test_query_builder_splits_multi_intent_requests():
    service = ConversationQueryService()
    semantic = SemanticConversation(
        intent="multi_part",
        subject=None,
        questions=[
            {"text": "What is the fee for Java?", "intent": "fee", "subject": "Java Programming"},
            {"text": "what are the batch timings for Python?", "intent": "timings", "subject": "Python Programming"},
        ],
        response_style="medium",
        requires_knowledge=True,
        wants_lead_action=False,
    )
    queries = service.build_queries(semantic=semantic, fallback_subject=None, original_message="mixed")
    assert len(queries) == 2
    assert "Java Programming" in queries[0]["query"]
    assert "Python Programming" in queries[1]["query"]
