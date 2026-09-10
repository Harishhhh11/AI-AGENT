from types import SimpleNamespace

from app.services.knowledge_answer_service import KnowledgeAnswerService


def item(title, content):
    return SimpleNamespace(title=title, content=content)


def test_topics_without_explicit_topics_heading_can_use_topic_lines():
    service = KnowledgeAnswerService()
    answer = service.answer(
        items=[
            item(
                "Python",
                "Python Programming\nVariables, functions, loops, OOP, APIs, and projects.",
            )
        ],
        intent="topics",
        subject="python",
        response_style="medium",
    )
    assert answer
    assert "Variables" in answer
    assert "functions" in answer
    assert "projects" in answer


def test_course_catalog_accepts_course_heading_and_title_fallback():
    service = KnowledgeAnswerService()
    answer = service.answer(
        items=[
            item("Python", "Course: Python Programming\nTopics: variables and functions."),
            item("Java", "Course - Core Java\nTopics: collections and OOP."),
        ],
        intent="company_courses",
        subject=None,
        response_style="medium",
    )
    assert answer
    assert "Python Programming" in answer
    assert "Core Java" in answer
