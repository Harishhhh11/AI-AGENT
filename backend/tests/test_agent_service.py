from types import SimpleNamespace

import pytest

from app.services.agent_service import AgentService


class FakeRepository:
    def __init__(self, existing=None):
        self.existing = existing
        self.items = []

    def get_by_slug(self, slug):
        return self.existing

    def get_by_id_in_organization(self, agent_id, organization_id):
        agent = self.existing
        if not agent:
            return None
        if agent.id != agent_id or agent.organization_id != organization_id:
            return None
        return agent

    def get_all_in_organization(self, organization_id):
        return [
            self.existing
        ] if self.existing and self.existing.organization_id == organization_id else []

    def add(self, agent):
        self.items.append(agent)


class FakeDB:
    def __init__(self):
        self.committed = False

    def commit(self):
        self.committed = True

    def refresh(self, obj):
        return obj


def make_service(existing=None):
    service = AgentService.__new__(AgentService)
    service.db = FakeDB()
    service.repository = FakeRepository(existing=existing)
    return service


def test_get_requires_matching_organization():
    agent = SimpleNamespace(id=1, organization_id=10)
    service = make_service(agent)

    assert service.get(1, 10) is agent
    assert service.get(1, 20) is None


def test_public_agent_requires_published_active_agent():
    org = SimpleNamespace(is_active=True)
    agent = SimpleNamespace(
        is_active=True,
        is_published=True,
        organization=org,
    )
    service = make_service(agent)

    assert service.get_public("demo") is agent

    agent.is_published = False
    assert service.get_public("demo") is None


def test_public_agent_rejects_inactive_organization():
    org = SimpleNamespace(is_active=False)
    agent = SimpleNamespace(
        is_active=True,
        is_published=True,
        organization=org,
    )
    service = make_service(agent)

    assert service.get_public("demo") is None


def test_create_rejects_duplicate_public_slug():
    existing = SimpleNamespace(public_slug="demo")
    service = make_service(existing)

    data = SimpleNamespace(
        name="Receptionist",
        public_slug="demo",
        welcome_message="Hello",
        system_instructions=None,
    )

    with pytest.raises(ValueError, match="public URL"):
        service.create(10, data)
