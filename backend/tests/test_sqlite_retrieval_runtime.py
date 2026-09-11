from types import SimpleNamespace


def test_sqlite_dialect_skips_pgvector_expression(monkeypatch):
    from app.services.knowledge_service import KnowledgeService

    class Dialect:
        name = "sqlite"

    class Bind:
        dialect = Dialect()

    class DB:
        bind = Bind()

    service = KnowledgeService.__new__(KnowledgeService)
    service.db = DB()
    service.embedding_service = SimpleNamespace(generate=lambda _: [0.0] * 384)

    class DummyEmbedding:
        def cosine_distance(self, _):
            raise AssertionError("pgvector cosine distance must not be built for SQLite")

    from app.models.knowledge_base import KnowledgeBase
    original_embedding = KnowledgeBase.embedding
    try:
        KnowledgeBase.embedding = DummyEmbedding()
        assert service._semantic_search(1, 13, "can i join online", 5) == []
    finally:
        KnowledgeBase.embedding = original_embedding
