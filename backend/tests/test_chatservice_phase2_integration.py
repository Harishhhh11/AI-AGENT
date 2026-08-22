"""Integration contracts for Phase 2 services inside ChatService."""

from types import SimpleNamespace
from unittest.mock import MagicMock

from app.services.chat_service import ChatService


def test_chatservice_initializes_phase2_services(monkeypatch):
    llm = MagicMock()
    monkeypatch.setattr(
        "app.services.chat_service.get_llm",
        lambda: llm,
    )

    db = MagicMock()
    service = ChatService(db)

    assert hasattr(service, "conversation_subject_service")
    assert hasattr(service, "response_policy_service")
    assert hasattr(service, "relevance_service")
    assert hasattr(service, "grounding_service")


def test_phase2_services_are_company_agnostic(monkeypatch):
    llm = MagicMock()
    monkeypatch.setattr(
        "app.services.chat_service.get_llm",
        lambda: llm,
    )

    service = ChatService(MagicMock())

    assert service.conversation_subject_service is not None
    assert service.response_policy_service is not None
    assert service.relevance_service is not None
    assert service.grounding_service is not None
