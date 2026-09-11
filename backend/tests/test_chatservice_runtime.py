from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.chat_service import ChatService


@pytest.mark.asyncio
async def test_chatservice_has_receptionist_fallback_prompt() -> None:
    service = ChatService.__new__(ChatService)
    lead = SimpleNamespace(
        name=None,
        phone=None,
        email=None,
        interest=None,
        preferred_mode=None,
        preferred_time=None,
    )

    prompt = service._build_receptionist_prompt(
        current_message="hello",
        message_type="general",
        current_subject=None,
        explicit_subject=None,
        previous_subject=None,
        intent="general",
        response_style="short",
        question_count=1,
        conversation_context="(none)",
        knowledge_context="",
        has_verified_knowledge=False,
        lead_context=lead,
        agent_instructions=None,
    )

    assert "hello" in prompt
    assert "Return only the customer-facing answer." in prompt
    assert "Lead context:" in prompt
