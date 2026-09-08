from types import SimpleNamespace

from app.services.retrieval_service import RetrievalService


def test_subject_filter_keeps_matching_knowledge_item() -> None:
    service = RetrievalService.__new__(RetrievalService)
    item = SimpleNamespace(
        title="MT-DOC",
        category="general",
        content="Course: Python Programming\nTopics: variables, functions, and AI",
    )

    result = service._filter_by_subject([item], "python")

    assert result == [item]
