from types import SimpleNamespace

from app.services.conversation_query_service import ConversationQueryService
from app.services.retrieval_service import RetrievalService


def test_explicit_online_is_mode():
    semantic = SimpleNamespace(intent="admission", subject="Python Programming", questions=[{"text": "Can I join online?", "intent": "admission", "subject": "Python Programming"}])
    queries = ConversationQueryService().build_queries(semantic=semantic, fallback_subject=None, original_message="Can I join online?")
    assert queries[0]["intent"] == "mode"


def test_retrieval_service_has_sqlite_safe_path():
    class Dialect:
        name = "sqlite"
    class Bind:
        dialect = Dialect()
    class DB:
        def get_bind(self):
            return Bind()
    item = SimpleNamespace(id=1, title="Python Programming", category="Programming", content="Training mode: Online", is_active=True)
    class Knowledge:
        db = DB()
        def get_all(self, **kwargs):
            return [item]
        def search(self, **kwargs):
            raise AssertionError("pgvector path must not run on sqlite")
    results = RetrievalService(Knowledge()).retrieve(1, "Python Programming online", subject="Python Programming", agent_id=13)
    assert results and results[0].id == 1
