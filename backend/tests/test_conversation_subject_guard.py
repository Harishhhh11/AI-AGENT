from types import SimpleNamespace

from app.services.conversation_guard import ConversationGuard
from app.services.retrieval_service import RetrievalService


def test_wrong_subject_is_rejected():
    python = SimpleNamespace(title="Python Programming", category="course", content="Python fundamentals")
    java = SimpleNamespace(title="Java Programming", category="course", content="Java fundamentals")
    assert ConversationGuard.matches_subject("python", python)
    assert not ConversationGuard.matches_subject("python", java)


def test_multi_word_subject_requires_majority_match():
    item = SimpleNamespace(title="Machine Learning", category="course", content="Supervised and unsupervised learning")
    unrelated = SimpleNamespace(title="Deep Learning", category="course", content="Neural networks")
    assert ConversationGuard.matches_subject("machine learning", item)
    assert not ConversationGuard.matches_subject("machine learning", unrelated)


def test_subject_is_added_only_when_missing_from_query():
    assert RetrievalService._build_query("What is the Python fee?", "python") == "What is the Python fee?"
    assert RetrievalService._build_query("What is the fee?", "python") == "python What is the fee?"
