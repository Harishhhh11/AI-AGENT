from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services.agent_service import AgentService
from app.services.chat_service import ChatService
from app.services.conversation_service import ConversationService
from app.services.lead_context_service import LeadContextService
from app.services.lead_extractor import LeadExtractor
from app.services.lead_service import LeadService
from app.schemas.lead import LeadCreate


def test_intent_detection_rejects_negated_requests():
    service = LeadContextService()

    assert service.detect_lead_intent("Please don't call me") is False
    assert service.detect_lead_intent("I am interested in Python") is True


def test_lead_answers_are_validated_without_losing_previous_state():
    service = LeadContextService()
    context = service.build_context(
        [
            {"role": "user", "content": "I want to join Python"},
            {"role": "assistant", "content": "May I know your name?"},
            {"role": "user", "content": "Ravi"},
            {"role": "assistant", "content": "Could you share your phone number?"},
            {"role": "user", "content": "not a phone number"},
        ]
    )

    assert context.name == "Ravi"
    assert context.phone is None
    assert service.get_next_missing_field(context) == "phone"


@pytest.mark.asyncio
async def test_llm_extraction_drops_invalid_field_but_keeps_valid_fields():
    extractor = LeadExtractor.__new__(LeadExtractor)
    extractor.llm = SimpleNamespace(
        generate_structured=AsyncMock(
            return_value='{"is_lead": true, "name": "Ravi", '
            '"phone": "not-a-number", "email": "ravi@example.com", '
            '"interest": "Python"}'
        )
    )

    is_lead, lead = await extractor.extract("I want to join Python")

    assert is_lead is True
    assert lead.name == "Ravi"
    assert lead.phone is None
    assert lead.email == "ravi@example.com"
    assert lead.interest == "Python"


@pytest.mark.asyncio
async def test_llm_extraction_falls_back_to_deterministic_parser():
    extractor = LeadExtractor.__new__(LeadExtractor)
    extractor.llm = SimpleNamespace(
        generate_structured=AsyncMock(side_effect=RuntimeError("offline"))
    )

    is_lead, lead = await extractor.extract(
        "I want to join Python. My name is Ravi and my email is ravi@example.com."
    )

    assert is_lead is True
    assert lead.name == "Ravi"
    assert lead.email == "ravi@example.com"


def test_chat_response_cleanup_removes_model_speaker_prefix():
    service = ChatService.__new__(ChatService)
    assert service._clean_response("Assistant: Welcome!") == "Welcome!"
    assert service._clean_response("AI Receptionist: Welcome!") == "Welcome!"


def test_foreign_session_id_is_not_reused_for_new_tenant():
    foreign = SimpleNamespace(
        organization_id=20,
        agent_id=4,
        session_id="shared-session",
    )

    class Repository:
        def __init__(self):
            self.created = None

        def get_by_session_id(self, session_id):
            return foreign if session_id == "shared-session" else None

        def add(self, conversation):
            self.created = conversation

    class DB:
        def __init__(self, repository):
            self.repository = repository

        def commit(self):
            self.repository.created.session_id = "new-session"

        def refresh(self, conversation):
            return conversation

    service = ConversationService.__new__(ConversationService)
    repository = Repository()
    service.repository = repository
    service.db = DB(repository)

    result = service.get_or_create_conversation(
        session_id="shared-session",
        organization_id=10,
        agent_id=4,
    )

    assert result is repository.created
    assert result.session_id != "shared-session"


def test_lead_upsert_uses_phone_and_email_keys():
    existing = SimpleNamespace(id=3, phone="9876543210", email="old@example.com")

    class Repository:
        def get_by_conversation_in_organization(self, conversation_id, organization_id):
            return None

        def get_by_phone_in_organization(self, phone, organization_id):
            return existing if phone == "9876543210" else None

        def get_by_email_in_organization(self, email, organization_id):
            return None

    class DB:
        def commit(self):
            pass

        def refresh(self, value):
            pass

    service = LeadService.__new__(LeadService)
    service.repository = Repository()
    service.db = DB()
    result = service.create_or_update_lead(
        lead_data=LeadCreate(name="New Name", phone="+91 98765 43210"),
        organization_id=7,
        conversation_id=8,
    )

    assert result is existing
    assert existing.name == "New Name"


def test_public_agent_slug_is_normalized_and_inactive_org_is_hidden():
    class Repository:
        def get_by_slug(self, slug):
            assert slug == "demo-agent"
            return SimpleNamespace(
                is_active=True,
                is_published=True,
                organization=SimpleNamespace(is_active=False),
            )

    service = AgentService.__new__(AgentService)
    service.repository = Repository()
    assert service.get_public(" Demo-Agent ") is None
