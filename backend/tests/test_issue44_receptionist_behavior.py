from types import SimpleNamespace

from app.services.chat_service import ChatService
from app.services.context_service import ContextService
from app.services.knowledge_answer_service import KnowledgeAnswerService
from app.services.lead_context_service import LeadContextService


def test_identity_question_is_not_company_retrieval():
    service = ChatService.__new__(ChatService)
    assert service._is_identity_question("Who are you?")
    assert service._is_identity_question("who are you/")
    assert service._identity_response().startswith("I'm Astra")


def test_common_indian_ten_digit_phone_is_valid():
    service = LeadContextService()
    assert service.extract_phone("9121401593") == "9121401593"


def test_topics_are_not_lead_intent():
    service = LeadContextService()
    assert not service.detect_lead_intent("Which topics do you cover?")


def test_factual_questions_do_not_require_lead_capture():
    context = ContextService()
    for message in (
        "Which topics do you cover?",
        "What is the duration of Python?",
        "What are the timings?",
        "What is the fee for Python?",
    ):
        analysis = context.analyze_message(message, messages=[])
        assert analysis["intent"] in {
            context.INTENT_TOPICS,
            context.INTENT_DURATION,
            context.INTENT_TIMINGS,
            context.INTENT_FEE,
        }


def test_tell_me_preserves_the_latest_customer_subject():
    context = ContextService()
    analysis = context.analyze_message(
        "tell me",
        messages=[
            {"role": "user", "content": "What are the timings for Python?"},
            {"role": "assistant", "content": "Monday to Friday, 10:00 AM to 11:00 AM IST."},
        ],
    )
    assert analysis["message_type"] == "follow_up"
    assert analysis["subject"] == "python"
    assert analysis["intent"] == context.INTENT_GENERAL
    assert analysis["retrieval_query"].lower().startswith("python tell me")


def test_fee_fact_answer_preserves_actual_value():
    service = KnowledgeAnswerService()
    result = service.answer(
        items=[SimpleNamespace(title="Python", content="The fee is INR 25,000.")],
        intent="fee",
        subject="python",
        response_style="short",
    )
    assert result == "Python: The fee is INR 25,000."


def test_timing_fact_answer_preserves_schedule():
    service = KnowledgeAnswerService()
    result = service.answer(
        items=[SimpleNamespace(title="Python", content="Class Schedule: Monday to Friday 10:00 AM to 11:00 AM IST")],
        intent="timings",
        subject="python",
        response_style="short",
    )
    assert result == "Python: Monday to Friday 10:00 AM to 11:00 AM IST"


def test_company_course_catalog_is_not_a_document_dump():
    service = KnowledgeAnswerService()
    result = service.answer(
        items=[
            SimpleNamespace(
                title="Company FAQ",
                content="Company: Maruthi Technologies. Course: Python Programming. Overview: Long description. Duration: 3 months. Fee: INR 8,000.",
            )
        ],
        intent="company_courses",
        subject=None,
        response_style="medium",
    )
    assert result == "We currently offer: Python Programming."
