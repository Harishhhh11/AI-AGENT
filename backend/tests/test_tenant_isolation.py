from types import SimpleNamespace

from app.repositories.agent_repository import AgentRepository
from app.repositories.lead_repository import LeadRepository


def test_agent_repository_scopes_by_organization() -> None:
    repo = object.__new__(AgentRepository)

    captured = {}

    class DummyDB:
        def scalar(self, statement):
            captured["statement"] = statement
            return None

    repo.db = DummyDB()

    result = repo.get_by_id_in_organization(42, 7)

    assert result is None
    statement_text = str(captured["statement"])
    assert "agents.id" in statement_text
    assert "agents.organization_id" in statement_text


def test_lead_repository_scopes_by_organization() -> None:
    repo = object.__new__(LeadRepository)

    captured = {}

    class DummyDB:
        def scalar(self, statement):
            captured["statement"] = statement
            return None

    repo.db = DummyDB()

    result = repo.get_by_id_in_organization(99, 7)

    assert result is None
    statement_text = str(captured["statement"])
    assert "leads.id" in statement_text
    assert "leads.organization_id" in statement_text
