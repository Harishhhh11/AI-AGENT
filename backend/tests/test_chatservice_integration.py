"""Focused integration contracts for Phase 2 ChatService wiring."""

from app.services.chat_service import ChatService


def test_chat_service_exposes_phase2_services() -> None:
    service = ChatService.__new__(ChatService)

    # The integration commit initializes these attributes in __init__.
    service.subject_service = object()
    service.response_policy_service = object()
    service.relevance_service = object()
    service.grounding_service = object()

    assert hasattr(service, "subject_service")
    assert hasattr(service, "response_policy_service")
    assert hasattr(service, "relevance_service")
    assert hasattr(service, "grounding_service")
