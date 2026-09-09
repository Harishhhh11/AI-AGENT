from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.services.agent_service import AgentService


class FakeScalarResult:
    def __init__(self, rows):
        self.rows = rows

    def all(self):
        return list(self.rows)


class FakeScalars:
    def __init__(self, rows):
        self.rows = rows

    def all(self):
        return list(self.rows)


class FakeDB:
    def __init__(self, knowledge=None):
        self.committed = False
        self.knowledge = list(knowledge or [])

    def scalars(self, statement):
        return FakeScalars(self.knowledge)

    def flush(self):
        return None

    def commit(self):
        self.committed = True

    def rollback(self):
        self.committed = False

    def refresh(self, obj):
        return obj


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
        return [self.existing] if self.existing and self.existing.organization_id == organization_id else []

    def add(self, agent):
        if getattr(agent, "id", None) is None:
            agent.id = 99
        self.items.append(agent)


def make_service(existing=None, knowledge=None):
    service = AgentService.__new__(AgentService)
    service.db = FakeDB(knowledge)
    service.repository = FakeRepository(existing=existing)
    return service


def test_get_requires_matching_organization():
    agent = SimpleNamespace(id=1, organization_id=10)
    service = make_service(agent)
    assert service.get(1, 10) is agent
    assert service.get(1, 20) is None


def test_public_agent_requires_published_active_agent():
    org = SimpleNamespace(is_active=True)
    agent = SimpleNamespace(is_active=True, is_published=True, organization=org)
    service = make_service(agent)
    assert service.get_public("demo") is agent
    agent.is_published = False
    assert service.get_public("demo") is None


def test_public_agent_rejects_inactive_organization():
    org = SimpleNamespace(is_active=False)
    agent = SimpleNamespace(is_active=True, is_published=True, organization=org)
    service = make_service(agent)
    assert service.get_public("demo") is None


def test_create_rejects_duplicate_public_slug():
    existing = SimpleNamespace(public_slug="demo")
    service = make_service(existing)
    data = SimpleNamespace(name="Receptionist", public_slug="demo", welcome_message="Hello", system_instructions=None, knowledge_item_ids=[])
    with pytest.raises(ValueError, match="public URL"):
        service.create(10, data)


def test_create_assigns_only_shared_selected_knowledge():
    item_one = SimpleNamespace(id=1, organization_id=10, agent_id=None, is_active=True, title="Python")
    item_two = SimpleNamespace(id=2, organization_id=10, agent_id=None, is_active=True, title="Java")
    service = make_service(knowledge=[item_one, item_two])
    data = SimpleNamespace(
        name="Admissions",
        public_slug="admissions",
        welcome_message="Hello",
        system_instructions=None,
        knowledge_item_ids=[1, 2],
    )
    agent = service.create(10, data)
    assert agent.id == 99
    assert item_one.agent_id == 99
    assert item_two.agent_id == 99
    assert service.db.committed is True


def test_create_rejects_item_already_private_to_another_agent():
    item = SimpleNamespace(id=1, organization_id=10, agent_id=5, is_active=True, title="Private data")
    service = make_service(knowledge=[item])
    data = SimpleNamespace(
        name="Admissions",
        public_slug="admissions",
        welcome_message="Hello",
        system_instructions=None,
        knowledge_item_ids=[1],
    )
    with pytest.raises(ValueError, match="already assigned"):
        service.create(10, data)


def test_set_knowledge_replaces_existing_selection():
    existing = SimpleNamespace(id=50, organization_id=10)
    old = SimpleNamespace(id=1, organization_id=10, agent_id=50, is_active=True, title="Old")
    new = SimpleNamespace(id=2, organization_id=10, agent_id=None, is_active=True, title="New")
    service = make_service(existing, knowledge=[new])

    original_scalars = service.db.scalars
    calls = []

    def scalars(statement):
        calls.append(statement)
        if len(calls) == 1:
            return FakeScalars([new])
        return FakeScalars([old])

    service.db.scalars = scalars
    result = service.set_knowledge(50, 10, [2])
    assert result is existing
    assert old.agent_id is None
    assert new.agent_id == 50
    assert service.db.committed is True
    service.db.scalars = original_scalars
