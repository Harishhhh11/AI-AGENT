from types import SimpleNamespace

from app.services.knowledge_ranker import KnowledgeRanker


def test_rank_prefers_lexically_grounded_subject_match():
    ranker = KnowledgeRanker()
    items = [
        SimpleNamespace(id=1, title="Java", content="Core Java and collections.", semantic_distance=0.10),
        SimpleNamespace(id=2, title="Python", content="Python covers variables, functions and OOP.", semantic_distance=0.30),
    ]
    result = ranker.rank(query="python topics", items=items, limit=2)
    assert result
    assert result[0].title == "Python"


def test_rank_rejects_unrelated_semantic_only_candidate():
    ranker = KnowledgeRanker()
    items = [SimpleNamespace(id=1, title="Java", content="Core Java and collections.", semantic_distance=0.01)]
    assert ranker.rank(query="python fees", items=items, limit=5) == []
