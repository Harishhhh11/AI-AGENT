"""Provider-neutral channel message contracts for Phase 5."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class InboundChannelMessage:
    channel: str
    external_user_id: str
    text: str
    organization_id: int
    conversation_key: str
    metadata: dict[str, Any] = field(default_factory=dict)
    received_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class OutboundChannelMessage:
    channel: str
    external_user_id: str
    text: str
    conversation_key: str
    metadata: dict[str, Any] = field(default_factory=dict)


class ChannelService:
    """Normalize channel traffic without embedding provider-specific behavior."""

    ALLOWED_CHANNELS = {"web", "whatsapp", "voice"}

    def normalize_inbound(
        self,
        *,
        channel: str,
        external_user_id: str,
        text: str,
        organization_id: int,
        conversation_key: str,
        metadata: dict[str, Any] | None = None,
    ) -> InboundChannelMessage:
        if channel not in self.ALLOWED_CHANNELS:
            raise ValueError(f"Unsupported channel: {channel}")
        if not external_user_id.strip():
            raise ValueError("external_user_id is required")
        if not text.strip():
            raise ValueError("text is required")
        if organization_id <= 0:
            raise ValueError("organization_id must be positive")
        if not conversation_key.strip():
            raise ValueError("conversation_key is required")
        return InboundChannelMessage(
            channel=channel,
            external_user_id=external_user_id,
            text=text.strip(),
            organization_id=organization_id,
            conversation_key=conversation_key,
            metadata=dict(metadata or {}),
        )

    def build_outbound(
        self,
        inbound: InboundChannelMessage,
        text: str,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> OutboundChannelMessage:
        if not text.strip():
            raise ValueError("text is required")
        return OutboundChannelMessage(
            channel=inbound.channel,
            external_user_id=inbound.external_user_id,
            text=text.strip(),
            conversation_key=inbound.conversation_key,
            metadata=dict(metadata or {}),
        )
