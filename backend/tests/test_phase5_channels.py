import pytest

from app.services.channel_service import ChannelService


def test_normalize_web_message():
    message = ChannelService().normalize_inbound(
        channel="web",
        external_user_id="user-1",
        text="  Hello  ",
        organization_id=1,
        conversation_key="web:user-1",
        metadata={"locale": "en"},
    )

    assert message.channel == "web"
    assert message.text == "Hello"
    assert message.conversation_key == "web:user-1"
    assert message.metadata["locale"] == "en"


def test_normalize_whatsapp_and_voice():
    service = ChannelService()

    whatsapp = service.normalize_inbound(
        channel="whatsapp",
        external_user_id="wa:+15550001111",
        text="Need pricing",
        organization_id=2,
        conversation_key="wa:+15550001111",
    )
    voice = service.normalize_inbound(
        channel="voice",
        external_user_id="call-22",
        text="Book a demo",
        organization_id=2,
        conversation_key="call:22",
    )

    assert whatsapp.channel == "whatsapp"
    assert voice.channel == "voice"


def test_unsupported_channel_is_rejected():
    with pytest.raises(ValueError, match="Unsupported channel"):
        ChannelService().normalize_inbound(
            channel="telegram",
            external_user_id="user-1",
            text="Hi",
            organization_id=1,
            conversation_key="telegram:user-1",
        )


def test_outbound_preserves_channel_identity():
    service = ChannelService()
    inbound = service.normalize_inbound(
        channel="whatsapp",
        external_user_id="wa:+15550001111",
        text="Hello",
        organization_id=1,
        conversation_key="wa:+15550001111",
    )

    outbound = service.build_outbound(inbound, "Thanks for contacting us.")

    assert outbound.channel == "whatsapp"
    assert outbound.external_user_id == inbound.external_user_id
    assert outbound.conversation_key == inbound.conversation_key
