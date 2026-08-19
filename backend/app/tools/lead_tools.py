"""Tools for durable lead operations."""

from __future__ import annotations

from typing import Any

from app.services.lead_service import LeadService
from app.tools.base import BaseTool, ToolContext, ToolResult


class SaveLeadTool(BaseTool):
    name = "save_lead"
    description = "Create or update the lead captured in the current conversation."
    requires_confirmation = False

    @property
    def input_schema(self) -> dict[str, Any]:
        return {"type": "object", "properties": {}, "additionalProperties": False}

    async def execute(
        self,
        context: ToolContext,
        arguments: dict[str, Any] | None = None,
    ) -> ToolResult:
        lead_context = context.lead_context
        if lead_context is None or not getattr(lead_context, "is_lead", False):
            return ToolResult(self.name, True, "No lead data needs saving.")

        lead = LeadService(context.db).save_context(
            context=lead_context,
            organization_id=context.organization_id,
            conversation_id=context.conversation_id,
        )
        if lead is None:
            return ToolResult(self.name, True, "No lead data needs saving.")

        return ToolResult(
            self.name,
            True,
            "Lead saved successfully.",
            data={"lead_id": lead.id, "status": lead.status},
        )
