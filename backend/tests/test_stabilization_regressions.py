"""Focused regression tests for stabilization fixes."""

from app.services.chat_service import ChatService
from app.services.lead_context_service import LeadContextService


def test_short_response_hard_ceiling() -> None:
    service = ChatService.__new__(ChatService)
    result = service._apply_response_length_guard(
        response="A" * 500,
        response_style="short",
    )
    assert len(result) <= ChatService.MAX_SHORT_RESPONSE_CHARS


def test_lead_interest_is_preserved_from_lead_intent() -> None:
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
    assert context.name == "David"


def test_lead_state_advances_without_losing_name() -> None:
    service = LeadContextService()
    context = service.build_context(
        [
            {"role": "user", "content": "I want to join Python"},
            {"role": "assistant", "content": "May I know your name?"},
            {"role": "user", "content": "David"},
            {"role": "assistant", "content": "Could you share your phone number?"},
            {"role": "user", "content": "1234"},
        ]
    )
    assert context.name == "David"
    assert context.phone is None
    assert service.get_next_missing_field(context) == "phone"


def test_lead_completes_only_after_email() -> None:
    service = LeadContextService()
    context = service.build_context(
        [
            {"role": "user", "content": "I want to join Python"},
            {"role": "assistant", "content": "May I know your name?"},
            {"role": "user", "content": "David"},
            {"role": "assistant", "content": "Could you share your phone number?"},
            {"role": "user", "content": "9121401593"},
            {"role": "assistant", "content": "Could you share your email address?"},
            {"role": "user", "content": "david@example.com"},
        ]
    )
    assert context.is_complete is True
    assert service.get_next_missing_field(context) is None
