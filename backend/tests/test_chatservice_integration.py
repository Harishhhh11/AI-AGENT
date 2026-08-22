"""Focused integration contracts for Phase 2 ChatService wiring."""

from unittest.mock import MagicMock, patch

from app.services.chat_service import ChatService


def test_chat_service_initializes_phase2_services() -> None:
    db = MagicMock()
    with patch("app.services.chat_service.get_llm", return_value=MagicMock()), \
        patch("app.services.chat_service.ConversationService"), \
        patch("app.services.chat_service.KnowledgeService"), \
        patch("app.services.chat_service.ContextService"), \
        patch("app.services.chat_service.LeadExtractor"), \
        patch("app.services.chat_service.LeadService"), \
        patch("app.services.chat_service.LeadContextService"), \
        patch("app.services.chat_service.ToolOrchestrator"):
        service = ChatService(db)

    assert service.conversation_subject_service.__class__.__name__ == "ConversationSubjectService"
    assert service.response_policy_service.__class__.__name__ == "ResponsePolicyService"
    assert service.relevance_service.__class__.__name__ == "RelevanceService"
    assert service.grounding_service.__class__.__name__ == "GroundingService"
