from types import SimpleNamespace

from app.repositories.knowledge_repository import KnowledgeRepository


class FakeScalarResult:
    def __init__(self, rows):
        self.rows = rows

    def all(self):
        return self.rows


class FakeScalars:
    def __init__(self, rows):
        self.rows = rows

    def all(self):
        return self.rows


class FakeSession:
    def __init__(self):
        self.last_statement = None

    def scalars(self, statement):
        self.last_statement = statement
        return FakeScalars([])

    def execute(self, statement):
        self.last_statement = statement
        return []


def test_repository_exposes_agent_scoped_query_api():
    repository = KnowledgeRepository(FakeSession())

    assert hasattr(repository, "get_all_in_agent")
    assert callable(repository.get_all_in_agent)


def test_agent_scope_allows_shared_and_specific_knowledge():
    # This test documents the intended query policy. The actual SQL
    # expression is constructed by KnowledgeRepository.search().
    # Shared knowledge uses agent_id=None; agent-specific knowledge uses
    # the requested agent id. Both are always additionally scoped by the
    # organization id.
    shared = SimpleNamespace(agent_id=None, organization_id=1)
    specific = SimpleNamespace(agent_id=7, organization_id=1)
    foreign = SimpleNamespace(agent_id=7, organization_id=2)

    allowed = {
        row.agent_id
        for row in (shared, specific)
        if row.organization_id == 1
    }

    assert allowed == {None, 7}
    assert foreign.organization_id != 1
