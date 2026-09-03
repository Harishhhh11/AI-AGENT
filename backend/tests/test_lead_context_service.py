from app.services.lead_context_service import LeadContextService


def test_lead_completion_requires_phone_and_email():
    service = LeadContextService()

    context = service.build_context(
        [
            {"role": "user", "content": "I want to join Python"},
            {"role": "assistant", "content": "May I know your name?"},
            {"role": "user", "content": "David"},
            {
                "role": "assistant",
                "content": "Could you share your phone number?",
            },
            {"role": "user", "content": "9121401593"},
        ]
    )

    assert context.is_lead is True
    assert context.interest == "I want to join Python"
    assert context.name == "David"
    assert context.phone == "9121401593"
    assert context.email is None
    assert context.is_complete is False
    assert service.get_next_missing_field(context) == "email"


def test_bare_name_is_bound_to_previous_name_question():
    service = LeadContextService()

    context = service.build_context(
        [
            {"role": "user", "content": "I want to join Python"},
            {"role": "assistant", "content": "May I know your name?"},
            {"role": "user", "content": "Harish"},
        ]
    )

    assert context.is_lead is True
    assert context.name == "Harish"


def test_invalid_phone_does_not_replace_valid_lead_state():
    service = LeadContextService()

    context = service.build_context(
        [
            {"role": "user", "content": "I want to join Python"},
            {"role": "assistant", "content": "May I know your name?"},
            {"role": "user", "content": "David"},
            {
                "role": "assistant",
                "content": "Could you share your phone number?",
            },
            {"role": "user", "content": "1234"},
        ]
    )

    assert context.name == "David"
    assert context.phone is None
    assert context.email is None
    assert context.is_complete is False
    assert service.get_next_missing_field(context) == "phone"


def test_email_completes_required_registration():
    service = LeadContextService()

    context = service.build_context(
        [
            {"role": "user", "content": "I want to join Python"},
            {"role": "assistant", "content": "May I know your name?"},
            {"role": "user", "content": "David"},
            {
                "role": "assistant",
                "content": "Could you share your phone number?",
            },
            {"role": "user", "content": "9121401593"},
            {
                "role": "assistant",
                "content": "Could you share your email address?",
            },
            {"role": "user", "content": "david@example.com"},
        ]
    )

    assert context.is_complete is True
    assert service.get_next_missing_field(context) is None


def test_generic_interested_message_does_not_become_name_or_interest():
    service = LeadContextService()

    context = service.build_context(
        [
            {
                "role": "user",
                "content": "I am interested in joining your services.",
            },
        ]
    )

    assert context.is_lead is True
    assert context.name is None
    assert context.interest is None
    assert service.get_next_missing_field(context) == "interest"
    assert service.get_next_question(context) == "Sure! What product or service are you interested in?"


def test_specific_interest_is_extracted_from_lead_intent():
    service = LeadContextService()

    context = service.build_context(
        [
            {"role": "user", "content": "I am interested in the Python course."},
        ]
    )

    assert context.is_lead is True
    assert context.name is None
    assert context.interest == "python course"
    assert service.get_next_missing_field(context) == "name"
