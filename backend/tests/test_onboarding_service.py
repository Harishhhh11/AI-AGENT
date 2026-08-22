"""Regression tests for company onboarding."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.services.onboarding_service import OnboardingService


class FakeSession:
    def __init__(self):
        self.objects = []
        self.flushed = False
        self.committed = False
        self.rolled_back = False

    def add(self, obj):
        self.objects.append(obj)

    def scalar(self, _statement):
        return None

    def flush(self):
        self.flushed = True
        next_id = 1
        for obj in self.objects:
            if getattr(obj, "id", None) is None:
                obj.id = next_id
                next_id += 1

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def refresh(self, _obj):
        return None


def build_service():
    db = FakeSession()
    service = OnboardingService.__new__(OnboardingService)
    service.db = db
    service.organizations = MagicMock()
    service.users = MagicMock()
    service.agents = MagicMock()
    service.organizations.get_by_name.return_value = None
    service.organizations.get_by_email.return_value = None
    service.users.get_by_email.return_value = None
    service.agents.get_by_slug.return_value = None
    return service, db


def build_request(**overrides):
    values = {
        "organization_name": "Acme Technologies",
        "organization_email": "owner@acme.example",
        "first_name": "Jane",
        "last_name": "Doe",
        "admin_email": "jane@acme.example",
        "password": "strong-password-123",
        "phone": "1234567890",
        "agent_name": "Acme Receptionist",
        "public_slug": "acme-receptionist",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_onboarding_creates_organization_admin_and_agent():
    service, db = build_service()

    organization, admin, agent = service.onboard(build_request())

    assert organization.name == "Acme Technologies"
    assert admin.organization_id == organization.id
    assert admin.email == "jane@acme.example"
    assert admin.is_superuser is True
    assert agent.organization_id == organization.id
    assert agent.public_slug == "acme-receptionist"
    assert agent.is_published is False
    assert db.flushed is True
    assert db.committed is True
    assert db.rolled_back is False


def test_onboarding_rejects_existing_organization_name():
    service, _db = build_service()
    service.organizations.get_by_name.return_value = object()

    with pytest.raises(ValueError, match="organization with this name already exists"):
        service.onboard(build_request())


def test_onboarding_rejects_existing_admin_email():
    service, _db = build_service()
    service.users.get_by_email.return_value = object()

    with pytest.raises(ValueError, match="user with this email already exists"):
        service.onboard(build_request())


def test_onboarding_rejects_existing_public_slug():
    service, _db = build_service()
    service.agents.get_by_slug.return_value = None
    service.agents.get_by_slug.return_value = object()

    with pytest.raises(ValueError, match="public agent URL is already in use"):
        service.onboard(build_request())


def test_onboarding_rolls_back_when_creation_fails():
    service, db = build_service()

    original_add = db.add
    calls = {"count": 0}

    def failing_add(obj):
        calls["count"] += 1
        if calls["count"] == 3:
            raise RuntimeError("agent creation failed")
        original_add(obj)

    db.add = failing_add

    with pytest.raises(RuntimeError, match="agent creation failed"):
        service.onboard(build_request())

    assert db.committed is False
    assert db.rolled_back is True
