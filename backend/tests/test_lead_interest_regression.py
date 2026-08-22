"""Focused regression test for deterministic lead-interest reconstruction."""

from app.services.lead_context_service import LeadContextService


def test_lead_intent_preserves_interest_without_changing_existing_lead_logic():
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
