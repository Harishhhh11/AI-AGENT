import pytest

from app.services.channel_agent_service import ChannelAgentService
from app.services.channel_service import ChannelService


class FakeResponder:
    async def respond(self, text: str, *, organization_id: int, conversation_key: str) -> str:
        return f"agent:{text}|org={organization_id}|key={conversation_key}"


@pytest.mark.asyncio
async def test_channel_message_reaches_agent_and_preserves_identity():
    service = ChannelAgentService(FakeResponder(), ChannelService())
    inbound = ChannelService().normalize_inbound(
        channel="whatsapp",
        external_user_id="+15550001111",
        text="Need pricing",
        organization_id=7,
        conversation_key="whatsapp:+15550001111",
    )

    result = await service.handle(inbound)

    assert result.outbound.channel == "whatsapp"
    assert result.outbound.external_user_id == "+15550001111"
    assert result.outbound.conversation_key == "whatsapp:+15550001111"
    assert "agent:Need pricing" in result.outbound.text
    assert "org=7" in result.outbound.text


@pytest.mark.asyncio
async def test_voice_message_uses_same_agent_boundary():
    service = ChannelAgentService(FakeResponder())
    inbound = ChannelService().normalize_inbound(
        channel="voice",
        external_user_id="caller-1",
        text="Book a demo",
        organization_id=3,
        conversation_key="voice:call-1",
    )

    result = await service.handle(inbound, metadata={"tts": True})

    assert result.outbound.channel == "voice"
    assert result.outbound.metadata["tts"] is True
    assert "agent:Book a demo" in result.outbound.text
