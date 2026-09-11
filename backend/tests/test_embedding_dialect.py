from types import SimpleNamespace


def test_sqlite_skips_pgvector_distance(monkeypatch):
    from app.services.knowledge_service import KnowledgeService
    from app.models.knowledge_base import KnowledgeBase

    class Dialect:
        name = "sqlite"

    class Bind:
        dialect = Dialect()

    class DummySession:
        bind = Bind()

    service = KnowledgeService.__new__(KnowledgeService)
    service.db = DummySession()
    service.embedding_service = SimpleNamespace(generate=lambda _: [0.0] * 384)

    class ForbiddenExpression:
        def cosine_distance(self, _):
            raise AssertionError("SQLite must never build pgvector <=> expressions")

    original = KnowledgeBase.embedding
    try:
        KnowledgeBase.embedding = ForbiddenExpression()
        assert service._semantic_search(1, 13, "Can I join online?", 5) == []
    finally:
        KnowledgeBase.embedding = original
