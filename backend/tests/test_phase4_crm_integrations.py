import pytest

from app.services.business_action_service import BusinessActionService


def test_business_action_is_provider_neutral_and_scoped():
    service = BusinessActionService()
    action = service.build_action(
        action_type="crm_sync",
        organization_id=12,
        lead_id=7,
        payload={"name": "Asha"},
    )
    assert action.status == "pending"
    assert action.organization_id == 12
    assert action.lead_id == 7
    assert action.payload["name"] == "Asha"


def test_business_action_rejects_unknown_provider_action():
    service = BusinessActionService()
    with pytest.raises(ValueError, match="Unsupported business action"):
        service.build_action(
            action_type="delete_everything",
            organization_id=12,
            lead_id=7,
        )


def test_business_action_completion_is_immutable():
    service = BusinessActionService()
    action = service.build_action(
        action_type="sheet_sync",
        organization_id=12,
        lead_id=7,
        payload={"row": 4},
    )
    completed = service.mark_completed(action)
    assert action.status == "pending"
    assert completed.status == "completed"


def test_failed_action_preserves_context_and_records_error():
    service = BusinessActionService()
    action = service.build_action(
        action_type="lead_follow_up",
        organization_id=12,
        lead_id=7,
    )
    failed = service.mark_failed(action, "provider unavailable")
    assert failed.status == "failed"
    assert failed.organization_id == 12
    assert failed.lead_id == 7
    assert failed.payload["error"] == "provider unavailable"
