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


def test_fee_answer_preserves_supporting_payment_detail():
    service = KnowledgeAnswerService()
    answer = service.answer(
        items=[item("Python", "The course fee is INR 25,000. Installments are available.")],
        intent="fee",
        subject="python",
        response_style="short",
    )
    assert answer == "Python: The course fee is INR 25,000. Installments are available."


def test_timing_answer_preserves_value_without_label_corruption():
    service = KnowledgeAnswerService()
    answer = service.answer(
        items=[item("Python", "Class Schedule: Monday to Friday 10:00 AM to 11:00 AM IST")],
        intent="timings",
        subject="python",
        response_style="short",
    )
    assert answer == "Python: Monday to Friday 10:00 AM to 11:00 AM IST."


def test_certificate_and_payment_answers_are_grounded():
    service = KnowledgeAnswerService()
    certificate = service.answer(
        items=[item("Java", "Completion certificate is provided after successful completion.")],
        intent="certificate",
        subject="java",
        response_style="short",
    )
    payment = service.answer(
        items=[item("Java", "Payment can be made in full or approved installments.")],
        intent="payment",
        subject="java",
        response_style="short",
    )
    assert certificate == "Java: Completion certificate is provided after successful completion."
    assert payment == "Java: Payment can be made in full or approved installments."


def test_online_mode_uses_source_prose():
    service = KnowledgeAnswerService()
    answer = service.answer(
        items=[item("Python", "Classes are available online and in the classroom.")],
        intent="mode",
        subject="python",
        response_style="short",
    )
    assert answer == "Python: Classes are available online and in the classroom."


def test_course_catalog_includes_content_heading_and_title_without_duplicates():
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
    assert "Python Programming" in answer
    assert "Core Java" in answer
    assert answer.count("Python Programming") == 1
    assert answer.count("Core Java") == 1
