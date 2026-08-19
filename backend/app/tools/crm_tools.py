"""CRM pipeline synchronization tool.

The tool uses a provider-neutral webhook contract so an organization can
connect HubSpot, Zoho, Salesforce, Pipedrive, or an automation platform
without making the receptionist depend on one vendor's SDK.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from app.config.settings import settings
from app.tools.base import BaseTool, ToolContext, ToolResult


class CRMSyncTool(BaseTool):
    """Upsert a saved lead to a configured CRM webhook."""

    name = "crm_sync"
    description = "Upsert the current lead into the configured CRM sales pipeline."
    requires_confirmation = False

    @property
    def input_schema(self) -> dict[str, Any]:
        return {"type": "object", "properties": {"lead_id": {"type": "integer"}}}

    def _configuration_error(self) -> str | None:
        if not settings.CRM_ENABLED:
            return "Set CRM_ENABLED=True to enable CRM synchronization."
        if not settings.CRM_WEBHOOK_URL:
            return "Set CRM_WEBHOOK_URL to your CRM or automation webhook URL."
        return None

    @staticmethod
    def _payload(context: ToolContext, lead: Any) -> dict[str, Any]:
        lead_id = getattr(lead, "id", None)
        conversation_id = context.conversation_id
        return {
            "event": "lead.upserted",
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "idempotency_key": f"lead:{context.organization_id}:{conversation_id}:{lead_id}",
            "organization_id": context.organization_id,
            "pipeline": {
                "name": settings.CRM_PIPELINE,
                "stage": settings.CRM_STAGE,
            },
            "lead": {
                "id": lead_id,
                "conversation_id": conversation_id,
                "name": getattr(lead, "name", None),
                "phone": getattr(lead, "phone", None),
                "email": getattr(lead, "email", None),
                "interest": getattr(lead, "interest", None),
                "preferred_mode": getattr(lead, "preferred_mode", None),
                "preferred_time": getattr(lead, "preferred_time", None),
                "notes": getattr(lead, "notes", None),
                "status": getattr(lead, "status", "new"),
            },
        }

    async def execute(
        self,
        context: ToolContext,
        arguments: dict[str, Any] | None = None,
    ) -> ToolResult:
        configuration_error = self._configuration_error()
        if configuration_error:
            return ToolResult(self.name, False, "CRM sync is not configured.", error=configuration_error)

        lead = context.metadata.get("lead") if context.metadata else None
        if lead is None:
            return ToolResult(self.name, False, "A persisted lead is required before CRM sync.", error="lead_missing")

        payload = self._payload(context, lead)
        headers = {
            "Content-Type": "application/json",
            "X-Idempotency-Key": payload["idempotency_key"],
        }
        if settings.CRM_API_KEY:
            headers["Authorization"] = f"Bearer {settings.CRM_API_KEY}"

        try:
            async with httpx.AsyncClient(timeout=settings.CRM_TIMEOUT_SECONDS) as client:
                response = await client.post(
                    settings.CRM_WEBHOOK_URL,
                    json=payload,
                    headers=headers,
                )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            return ToolResult(self.name, False, "CRM sync failed.", error=str(exc))

        return ToolResult(
            self.name,
            True,
            "Lead synced to CRM.",
            data={
                "lead_id": getattr(lead, "id", None),
                "pipeline": settings.CRM_PIPELINE,
                "stage": settings.CRM_STAGE,
                "status_code": response.status_code,
            },
        )
