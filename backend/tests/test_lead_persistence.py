from types import SimpleNamespace
from unittest.mock import Mock

from app.services.lead_context_service import LeadContext
from app.services.lead_context_service import LeadContextService
from app.services.lead_service import LeadService


def test_save_context_maps_stable_state_to_one_upsert():
    service = LeadService.__new__(LeadService)
    service.create_or_update_lead = Mock(
        return_value="saved-lead"
    )

    context = LeadContext(
        is_lead=True,
        name="Harish",
        phone="9121401593",
        email="harish@example.com",
        interest="Python",
        preferred_mode="online",
        preferred_time="10 AM",
        notes="Interested in the next batch",
    )

    result = service.save_context(
        context=context,
        organization_id=7,
        conversation_id=42,
    )

    assert result == "saved-lead"
    service.create_or_update_lead.assert_called_once()

    call = service.create_or_update_lead.call_args.kwargs

    assert call["organization_id"] == 7
    assert call["conversation_id"] == 42
    assert call["lead_data"].name == "Harish"
    assert call["lead_data"].phone == "9121401593"
    assert call["lead_data"].email == "harish@example.com"
    assert call["lead_data"].interest == "Python"
    assert call["lead_data"].preferred_mode == "online"
    assert call["lead_data"].preferred_time == "10 AM"
    assert call["lead_data"].notes == "Interested in the next batch"


def test_save_context_ignores_non_leads():
    service = LeadService.__new__(LeadService)
    service.create_or_update_lead = Mock()

    result = service.save_context(
        context=LeadContext(),
        organization_id=7,
        conversation_id=42,
    )

    assert result is None
    service.create_or_update_lead.assert_not_called()


def test_persisted_lead_rehydrates_complete_context():
    persisted_lead = SimpleNamespace(
        name="Harish",
        phone="9121401593",
        email="harish@example.com",
        interest="Python",
        preferred_mode="online",
        preferred_time="10 AM",
        notes="Interested in the next batch",
    )

    context = LeadContextService().build_context(
        conversation=[],
        extracted_lead=persisted_lead,
    )

    assert context.is_lead is True
    assert context.is_complete is True
    assert context.name == "Harish"
    assert context.phone == "9121401593"
    assert context.email == "harish@example.com"
    assert context.interest == "Python"
    assert LeadContextService().get_next_missing_field(context) is None
