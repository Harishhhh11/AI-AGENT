from types import SimpleNamespace

from app.services.conversation_query_service import ConversationQueryService
from app.services.retrieval_service import RetrievalService


class FakeDialect:
    name = "sqlite"


class FakeBind:
    dialect = FakeDialect()


class FakeDB:
    def get_bind(self):
        return FakeBind()


class FakeKnowledgeService:
    def __init__(self):
        self.db = FakeDB()
        self.items = [
            SimpleNamespace(
                id=1,
                title="Python Programming",
                category="Programming",
                content="Duration: 3 months. Training mode: Online and classroom. Topics: Python syntax and fundamentals.",
                is_active=True,
            )
        ]

    def get_all(self, organization_id, agent_id=None, scope="all"):
        assert organization_id == 1
        assert agent_id == 13
        assert scope == "available"
        return self.items

    def search(self, **kwargs):
        raise AssertionError("SQLite retrieval must not call the pgvector search path")


def test_sqlite_retrieval_avoids_pgvector_operator_and_uses_scoped_rows():
    service = RetrievalService(FakeKnowledgeService())
    results = service.retrieve(
        organization_id=1,
        agent_id=13,
        query="Python Programming mode online",
        subject="Python Programming",
        limit=4,
    )
    assert results
    assert results[0].title == "Python Programming"


def test_query_service_maps_explicit_online_question_to_mode():
    semantic = SimpleNamespace(
        intent="admission",
        subject="Python Programming",
        questions=[
            {"text": "Can I join online?", "intent": "admission", "subject": "Python Programming"}
        ],
    )
    queries = ConversationQueryService().build_queries(
        semantic=semantic,
        fallback_subject=None,
        original_message="Can I join online?",
    )
    assert queries[0]["intent"] == "mode"
    assert "online" in queries[0]["query"].lower()
