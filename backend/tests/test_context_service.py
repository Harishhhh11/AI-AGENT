from app.services.context_service import ContextService


def test_company_wide_courses_request() -> None:
    service = ContextService()

    assert service.classify_message("What courses do you offer?") == "company_general"


def test_fee_follow_up_requires_previous_subject() -> None:
    service = ContextService()

    analysis = service.analyze_message(
        "How much?",
        messages=[
            {"role": "user", "content": "Do you offer Python?"},
            {"role": "assistant", "content": "Yes, we offer Python."},
        ],
    )

    assert analysis["message_type"] == "follow_up"
    assert analysis["intent"] == service.INTENT_FEE
    assert analysis["subject"] == "python"


def test_topic_switches_from_python_to_data_science() -> None:
    service = ContextService()

    analysis = service.analyze_message(
        "What about Data Science?",
        messages=[
            {"role": "user", "content": "Tell me about Python."},
            {"role": "assistant", "content": "Sure."},
        ],
    )

    assert analysis["message_type"] == "new_topic"
    assert analysis["subject"] == "data science"


def test_response_style_scales_with_question_complexity() -> None:
    service = ContextService()

    short = service.analyze_message(
        "How much is Python?",
        messages=[],
    )
    long = service.analyze_message(
        "Give me complete details about the Python course including topics, duration, timings, eligibility and admission information.",
        messages=[],
    )

    assert short["response_style"] == "short"
    assert long["response_style"] in {"medium", "long"}


def test_unrelated_question_is_not_treated_as_company_subject() -> None:
    service = ContextService()

    analysis = service.analyze_message(
        "What is the weather today?",
        messages=[],
    )

    assert analysis["message_type"] == "general"
    assert analysis["requires_knowledge"] is False
