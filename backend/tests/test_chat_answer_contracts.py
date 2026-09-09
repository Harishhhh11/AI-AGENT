from types import SimpleNamespace

from app.services.knowledge_answer_service import KnowledgeAnswerService


def test_answer_contains_verified_fee_detail():
    service = KnowledgeAnswerService()
    result = service.answer(
        items=[SimpleNamespace(title="Python", content="The course fee is INR 25,000. Installments are available.")],
        intent="fee",
        subject="python",
        response_style="short",
    )
    assert result == "Python: The course fee is INR 25,000. Installments are available."


def test_answer_supports_follow_up_topics_without_subject_repetition():
    service = KnowledgeAnswerService()
    result = service.answer(
        items=[SimpleNamespace(title="Python", content="Topics include variables, functions, OOP, APIs, testing, and projects.")],
        intent="topics",
        subject="python",
        response_style="medium",
    )
    assert "functions" in result
    assert "testing" in result


def test_answer_handles_multiple_questions_with_full_context_items():
    service = KnowledgeAnswerService()
    result = service.answer(
        items=[SimpleNamespace(title="Python", content="Fee is INR 25,000. Duration is 12 weeks. Online and classroom modes are available.")],
        intent="details",
        subject="python",
        response_style="long",
    )
    assert "Fee is INR 25,000" in result
    assert "12 weeks" in result
    assert "classroom" in result
