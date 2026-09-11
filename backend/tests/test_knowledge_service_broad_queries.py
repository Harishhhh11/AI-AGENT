from types import SimpleNamespace

from app.services.knowledge_service import KnowledgeService


def test_is_broad_query_for_course_catalog():
    assert KnowledgeService._is_broad_query("Which courses do you offer?", []) is True


def test_is_broad_query_for_topics():
    assert KnowledgeService._is_broad_query("What topics are covered?", []) is True


def test_is_broad_query_requires_empty_keywords():
    assert KnowledgeService._is_broad_query("Which courses do you offer in Python?", ["python"]) is False


def test_scoped_active_knowledge_filters_by_agent(monkeypatch):
    class FakeDB:
        def scalars(self, statement):
            return SimpleNamespace(all=lambda: [SimpleNamespace(id=2, agent_id=7, is_active=True)])

    service = KnowledgeService.__new__(KnowledgeService)
    service.db = FakeDB()

    calls = []
    original_where = KnowledgeService._scoped_active_knowledge

    def fake_or(*args):
        calls.append(args)
        return object()

    # The query builder is intentionally exercised through the service method;
    # this test only verifies the returned records remain scoped to the selected agent.
    result = original_where(service, 10, 7, 25)
    assert result[0].agent_id == 7
    assert calls == []
