from app.services.relevance_service import RelevanceService


def test_plural_question_matches_singular_knowledge_label() -> None:
    result = RelevanceService().score(
        query="Which courses do you offer?",
        title="MT-DOC",
        content="Course: Python Programming",
    )

    assert result.accepted is True
