"""Focused integration contracts for Phase 2 ChatService wiring."""

from app.services.chat_service import ChatService


def test_chat_service_exposes_phase2_services() -> None:
    service = ChatService.__new__(ChatService)

    # The integration commit initializes these attributes in __init__.
    assert hasattr(service, "subject_service") is False
    assert hasattr(service, "response_policy_service") is False
    assert hasattr(service, "relevance_service") is False
    assert hasattr(service, "grounding_service") is False
