import pytest

from app.services.channel_service import ChannelService
from app.services.provider_adapter_service import VoiceAdapter, WhatsAppAdapter


def test_whatsapp_inbound_adapter():
    adapter = WhatsAppAdapter(ChannelService())
    message = adapter.inbound(
        {
            "from": "+15550001111",
            "message_id": "wamid-1",
            "message": {"text": "Need a demo"},
        },
        organization_id=1,
    )

    assert message.channel == "whatsapp"
    assert message.external_user_id == "+15550001111"
    assert message.text == "Need a demo"
    assert message.conversation_key == "whatsapp:+15550001111"


def test_whatsapp_outbound_is_provider_envelope():
    adapter = WhatsAppAdapter()
    inbound = adapter.inbound(
        {
            "from": "+15550001111",
            "message": {"text": "Hello"},
        },
        organization_id=1,
    )
    outbound = adapter.channel_service.build_outbound(inbound, "Thanks")
    envelope = adapter.outbound(outbound)

    assert envelope.provider == "whatsapp"
    assert envelope.payload["to"] == "+15550001111"
    assert envelope.payload["text"]["body"] == "Thanks"


def test_voice_inbound_adapter():
    adapter = VoiceAdapter()
    message = adapter.inbound(
        {
            "caller_id": "+15550002222",
            "call_id": "call-9",
            "transcript": "Book a call",
            "duration_seconds": 22,
        },
        organization_id=2,
    )

    assert message.channel == "voice"
    assert message.text == "Book a call"
    assert message.conversation_key == "voice:call-9"
    assert message.metadata["duration_seconds"] == 22


def test_provider_specific_outbound_channel_is_rejected():
    adapter = VoiceAdapter()
    whatsapp_message = ChannelService().normalize_inbound(
        channel="whatsapp",
        external_user_id="+15550001111",
        text="Hi",
        organization_id=1,
        conversation_key="whatsapp:+15550001111",
    )
    outbound = ChannelService().build_outbound(whatsapp_message, "Hi")

    with pytest.raises(ValueError, match="Voice adapter"):
        adapter.outbound(outbound)
