"""Concrete-safe provider adapters for WhatsApp and voice channels."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services.channel_service import ChannelService, InboundChannelMessage, OutboundChannelMessage


@dataclass(frozen=True)
class ProviderEnvelope:
    provider: str
    channel: str
    payload: dict[str, Any]


class WhatsAppAdapter:
    """Translate provider-shaped WhatsApp payloads without sending network requests."""

    provider = "whatsapp"

    def __init__(self, channel_service: ChannelService | None = None) -> None:
        self.channel_service = channel_service or ChannelService()

    def inbound(
        self,
        payload: dict[str, Any],
        *,
        organization_id: int,
    ) -> InboundChannelMessage:
        sender = str(payload.get("from", ""))
        message = payload.get("message") or {}
        text = str(message.get("text", ""))
        message_id = str(payload.get("message_id", ""))
        return self.channel_service.normalize_inbound(
            channel="whatsapp",
            external_user_id=sender,
            text=text,
            organization_id=organization_id,
            conversation_key=f"whatsapp:{sender}",
            metadata={
                "provider": self.provider,
                "message_id": message_id,
            },
        )

    def outbound(self, message: OutboundChannelMessage) -> ProviderEnvelope:
        if message.channel != "whatsapp":
            raise ValueError("WhatsApp adapter requires a WhatsApp message")
        return ProviderEnvelope(
            provider=self.provider,
            channel="whatsapp",
            payload={
                "to": message.external_user_id,
                "type": "text",
                "text": {"body": message.text},
                "conversation_key": message.conversation_key,
            },
        )


class VoiceAdapter:
    """Translate provider-shaped voice session payloads without starting a live call."""

    provider = "voice"

    def __init__(self, channel_service: ChannelService | None = None) -> None:
        self.channel_service = channel_service or ChannelService()

    def inbound(
        self,
        payload: dict[str, Any],
        *,
        organization_id: int,
    ) -> InboundChannelMessage:
        caller = str(payload.get("caller_id", ""))
        transcript = str(payload.get("transcript", ""))
        call_id = str(payload.get("call_id", ""))
        return self.channel_service.normalize_inbound(
            channel="voice",
            external_user_id=caller,
            text=transcript,
            organization_id=organization_id,
            conversation_key=f"voice:{call_id or caller}",
            metadata={
                "provider": self.provider,
                "call_id": call_id,
                "duration_seconds": payload.get("duration_seconds"),
            },
        )

    def outbound(self, message: OutboundChannelMessage) -> ProviderEnvelope:
        if message.channel != "voice":
            raise ValueError("Voice adapter requires a voice message")
        return ProviderEnvelope(
            provider=self.provider,
            channel="voice",
            payload={
                "caller_id": message.external_user_id,
                "text": message.text,
                "conversation_key": message.conversation_key,
            },
        )
