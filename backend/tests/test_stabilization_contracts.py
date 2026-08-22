"""Stabilization contracts for legacy receptionist behavior."""

from app.services.chat_service import ChatService
from app.services.lead_context_service import LeadContextService


def test_response_guard_must_never_exceed_short_limit() -> None:
    service = ChatService.__new__(ChatService)
    result = service._apply_response_length_guard(
        response="A" * 500,
        response_style="short",
    )
    assert len(result) <= ChatService.MAX_SHORT_RESPONSE_CHARS


def test_lead_intent_preserves_initial_interest() -> None:
    service = LeadContextService()
    context = service.build_context(
        [
            {"role": "user", "content": "I want to join Python"},
            {"role": "assistant", "content": "May I know your name?"},
            {"role": "user", "content": "David"},
        ]
    )
    assert context.is_lead is True
    assert context.interest == "I want to join Python"


def test_lead_field_order_advances_to_phone_after_name() -> None:
    service = LeadContextService()
    context = service.build_context(
        [
            {"role": "user", "content": "I want to join Python"},
            {"role": "assistant", "content": "May I know your name?"},
            {"role": "user", "content": "David"},
        ]
    )
    assert service.get_next_missing_field(context) == "phone"
