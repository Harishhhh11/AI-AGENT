from types import SimpleNamespace

import pytest

from app.services.lead_lifecycle_service import LeadLifecycleService


class FakeLeadService:
    def __init__(self):
        self.lead = SimpleNamespace(id=7, status="new")
        self.updated = []

    def get_lead(self, lead_id, organization_id):
        return self.lead if lead_id == 7 and organization_id == 1 else None

    def update_status(self, lead_id, organization_id, status):
        self.lead.status = status
        self.updated.append((lead_id, organization_id, status))
        return self.lead


def test_lifecycle_allows_forward_progression():
    service = LeadLifecycleService(FakeLeadService())
    result = service.transition(lead_id=7, organization_id=1, target_status="contacted")
    assert result.from_status == "new"
    assert result.to_status == "contacted"
    assert result.changed is True


def test_lifecycle_rejects_backward_transition():
    fake = FakeLeadService()
    fake.lead.status = "qualified"
    service = LeadLifecycleService(fake)
    with pytest.raises(ValueError, match="Invalid lifecycle transition"):
        service.transition(lead_id=7, organization_id=1, target_status="contacted")


def test_lifecycle_allows_lost_terminal_transition():
    service = LeadLifecycleService(FakeLeadService())
    result = service.transition(lead_id=7, organization_id=1, target_status="lost")
    assert result.changed is True
    assert result.to_status == "lost"


def test_missing_lead_is_safe_noop():
    service = LeadLifecycleService(FakeLeadService())
    result = service.transition(lead_id=999, organization_id=1, target_status="contacted")
    assert result.changed is False
    assert result.lead_id is None
