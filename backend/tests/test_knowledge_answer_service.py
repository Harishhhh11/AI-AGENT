from types import SimpleNamespace

from app.services.knowledge_answer_service import KnowledgeAnswerService


def item(title, content):
    return SimpleNamespace(title=title, content=content)


def test_topics_answer_keeps_multiple_topic_sentences():
    service = KnowledgeAnswerService()
    answer = service.answer(
        items=[item("Python", "Topics include variables, functions, OOP, APIs, and projects.")],
        intent="topics",
        subject="python",
        response_style="medium",
    )
    assert answer
    assert "variables" in answer
    assert "OOP" in answer
    assert "projects" in answer


def test_company_courses_answer_keeps_multiple_items():
    service = KnowledgeAnswerService()
    answer = service.answer(
        items=[
            item("Python", "Python course covers fundamentals and projects."),
            item("Java", "Java course covers core Java and collections."),
            item("Data Analytics", "Data Analytics course covers Excel and Power BI."),
        ],
        intent="company_courses",
        subject=None,
        response_style="medium",
    )
    assert answer
    assert "Python" in answer
    assert "Java" in answer
    assert "Data Analytics" in answer


def test_fee_answer_does_not_duplicate_same_fact():
    service = KnowledgeAnswerService()
    answer = service.answer(
        items=[
            item("Python", "The fee is INR 25,000."),
            item("Python fees", "The fee is INR 25,000."),
        ],
        intent="fee",
        subject="python",
        response_style="short",
    )
    assert answer == "Python: The fee is INR 25,000."
