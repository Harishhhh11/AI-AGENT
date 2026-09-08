from types import SimpleNamespace
from unittest.mock import MagicMock

from app.services.knowledge_answer_service import KnowledgeAnswerService
from app.services.retrieval_service import RetrievalService


def test_company_courses_answer_contains_all_available_course_entries():
    service = KnowledgeAnswerService()
    items = [
        SimpleNamespace(title="Python Programming", content="Python covers fundamentals, functions, OOP, and practical projects."),
        SimpleNamespace(title="Java Programming", content="Java covers core Java, OOP, collections, and practical projects."),
    ]

    answer = service.answer(
        items=items,
        intent="company_courses",
        subject=None,
        response_style="medium",
    )

    assert answer
    assert "Python Programming" in answer
    assert "Java Programming" in answer


def test_topics_answer_keeps_the_full_topic_content():
    service = KnowledgeAnswerService()
    items = [
        SimpleNamespace(
            title="Python Programming",
            content="Python covers variables, data types, functions, OOP, file handling, and practical projects.",
        )
    ]

    answer = service.answer(
        items=items,
        intent="topics",
        subject="python",
        response_style="medium",
    )

    assert answer
    assert "variables" in answer
    assert "file handling" in answer
    assert "practical projects" in answer


def test_retrieval_preserves_multiple_candidates_for_a_company_wide_query():
    knowledge_service = MagicMock()
    knowledge_service.search.return_value = [
        SimpleNamespace(id=1, title="Python Programming", category="course", content="Python course details"),
        SimpleNamespace(id=2, title="Java Programming", category="course", content="Java course details"),
    ]

    service = RetrievalService(knowledge_service)
    result = service.retrieve(
        organization_id=2,
        query="Which courses do you offer?",
        limit=5,
        subject=None,
        agent_id=10,
    )

    assert len(result) == 2
    assert {item.title for item in result} == {"Python Programming", "Java Programming"}
