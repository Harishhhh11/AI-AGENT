from types import SimpleNamespace

from app.services.knowledge_ranker import KnowledgeRanker


def test_rank_prefers_title_match_over_weak_candidate():
    ranker = KnowledgeRanker()
    exact = SimpleNamespace(id=1, title="Python Course", category="training", content="Complete Python curriculum")
    weak = SimpleNamespace(id=2, title="General Programming", category="training", content="Software development overview")
    result = ranker.rank(query="python course fee", items=[weak, exact], limit=2)
    assert result[0] is exact


def test_rank_is_deterministic_for_same_scores():
    ranker = KnowledgeRanker()
    first = SimpleNamespace(id=1, title="Alpha", category="", content="python")
    second = SimpleNamespace(id=2, title="Beta", category="", content="python")
    result = ranker.rank(query="python", items=[first, second], limit=2)
    assert result == [second, first]


def test_rank_uses_semantic_signal_when_lexical_scores_are_equal():
    ranker = KnowledgeRanker()
    first = SimpleNamespace(id=1, title="Online classes", category="training", content="Join remotely", semantic_distance=0.45)
    second = SimpleNamespace(id=2, title="Online classes", category="training", content="Join remotely", semantic_distance=0.20)
    result = ranker.rank(query="remote learning", items=[first, second], limit=2)
    assert result[0] is second
