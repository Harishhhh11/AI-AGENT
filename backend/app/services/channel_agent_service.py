"""Connect Phase 5 channel messages to the existing agent boundary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from app.services.channel_service import InboundChannelMessage, OutboundChannelMessage, ChannelService


class AgentResponder(Protocol):
    async def respond(self, text: str, *, organization_id: int, conversation_key: str) -> str:
        ...


@dataclass(frozen=True)
class ChannelAgentResult:
    inbound: InboundChannelMessage
    outbound: OutboundChannelMessage


class ChannelAgentService:
    """Keep channel concerns outside ChatService while preserving conversation identity."""

    def __init__(self, responder: AgentResponder, channel_service: ChannelService | None = None) -> None:
        self.responder = responder
        self.channel_service = channel_service or ChannelService()

    async def handle(
        self,
        inbound: InboundChannelMessage,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> ChannelAgentResult:
        response_text = await self.responder.respond(
            inbound.text,
            organization_id=inbound.organization_id,
            conversation_key=inbound.conversation_key,
        )
        outbound = self.channel_service.build_outbound(
            inbound,
            response_text,
            metadata=metadata,
        )
        return ChannelAgentResult(inbound=inbound, outbound=outbound)
