from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.chat_service import ChatService


@dataclass
class FakeConversation:
    id: int = 1
    session_id: str = "session-1"


def build_service() -> ChatService:
    service = object.__new__(ChatService)
    service.conversation_service = MagicMock()
    service.context_service = MagicMock()
    service.lead_context_service = MagicMock()
    service.lead_service = MagicMock()
    service.tool_orchestrator = MagicMock()
    service.llm = MagicMock()
    return service


@pytest.mark.asyncio
async def test_blank_message_returns_help_prompt() -> None:
    service = build_service()

    session_id, response = await service.generate_response(
        message="   ",
        organization_id=1,
        session_id="session-1",
    )

    assert session_id == "session-1"
    assert response == "How can I help you?"
    service.conversation_service.get_or_create_conversation.assert_not_called()


def test_short_response_limit_is_not_too_long() -> None:
    service = ChatService.__new__(ChatService)
    text = "A" * 500

    result = service._apply_response_length_guard(
        response=text,
        response_style="short",
    )

    assert len(result) <= ChatService.MAX_SHORT_RESPONSE_CHARS


def test_response_cleanup_removes_internal_prefix() -> None:
    service = ChatService.__new__(ChatService)

    result = service._clean_response(
        "Assistant: The Python course is ₹8,000."
    )

    assert result == "The Python course is ₹8,000."
