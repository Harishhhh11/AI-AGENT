from types import SimpleNamespace
from unittest.mock import MagicMock

from app.services.chat_service import ChatService
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
        response_style="short",
    )

    assert answer
    assert "Python Programming" in answer
    assert "Java Programming" in answer


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


def test_chat_grounding_does_not_drop_company_wide_items_on_generic_query():
    service = ChatService.__new__(ChatService)
    service.knowledge_answer_service = KnowledgeAnswerService()
    service.retrieval_service = MagicMock()
    service.grounding_service = MagicMock()
    service.grounding_service.evaluate.side_effect = lambda **kwargs: SimpleNamespace(accepted=True)

    items = [
        SimpleNamespace(title="Python Programming", content="Python covers fundamentals and OOP."),
        SimpleNamespace(title="Java Programming", content="Java covers core Java and OOP."),
    ]
    service.retrieval_service.retrieve.return_value = items

    result = service.knowledge_answer_service.answer(
        items=items,
        intent="company_courses",
        subject=None,
        response_style="short",
    )

    assert "Python Programming" in result
    assert "Java Programming" in result
