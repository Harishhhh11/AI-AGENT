from types import SimpleNamespace

from app.services.conversation_guard import ConversationGuard
from app.services.retrieval_service import RetrievalService


def test_subject_guard_rejects_wrong_course():
    python = SimpleNamespace(title="Python Programming", category="course", content="Python fundamentals")
    java = SimpleNamespace(title="Java Programming", category="course", content="Java fundamentals")
    assert ConversationGuard.matches_subject("python", python)
    assert not ConversationGuard.matches_subject("python", java)


def test_subject_guard_accepts_multi_word_subject_with_majority_match():
    item = SimpleNamespace(title="Machine Learning", category="course", content="Supervised and unsupervised learning")
    assert ConversationGuard.matches_subject("machine learning", item)


def test_retrieval_build_query_does_not_duplicate_subject():
    assert RetrievalService._build_query("What is the Python fee?", "python") == "What is the Python fee?"
    assert RetrievalService._build_query("What is the fee?", "python") == "python What is the fee?"
