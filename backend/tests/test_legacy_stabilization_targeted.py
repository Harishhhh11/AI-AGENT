"""Targeted regression contracts for legacy stabilization."""

from app.services.lead_context_service import LeadContextService


def test_lead_interest_is_reconstructed_from_initial_intent() -> None:
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
    assert service.get_next_missing_field(context) == "phone"
