"""Provider-backed tools used by the receptionist agent."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config.settings import settings
from app.tools.base import BaseTool, ToolContext, ToolResult
from app.tools.crm_tools import CRMSyncTool


class GoogleSheetTool(BaseTool):
    """Idempotently upsert a lead into a configured Google Sheet.

    The first three columns form a stable key (organization + conversation),
    so repeated lead updates revise the existing row instead of appending a
    new row for every chat message.
    """

    name = "google_sheet"
    description = "Upsert the current lead into the organization's Google Sheet."
    requires_confirmation = False
    headers = [
        "lead_id", "organization_id", "conversation_id", "name", "phone",
        "email", "interest", "preferred_mode", "preferred_time", "notes", "status", "updated_at",
    ]

    @property
    def input_schema(self) -> dict[str, Any]:
        return {"type": "object", "properties": {"lead_id": {"type": "integer"}}}

    def _configuration_error(self) -> str | None:
        if not settings.GOOGLE_SHEETS_ENABLED:
            return "Set GOOGLE_SHEETS_ENABLED=True to enable Google Sheets sync."
        if not settings.GOOGLE_SHEET_ID:
            return "Set GOOGLE_SHEET_ID to the destination spreadsheet ID."
        if not settings.GOOGLE_SHEETS_CREDENTIALS_JSON:
            return "Set GOOGLE_SHEETS_CREDENTIALS_JSON to a service-account JSON string or file path."
        return None

    def _build_service(self):
        # Lazy imports keep the backend usable when this optional integration
        # is not installed or configured.
        try:
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "Google Sheets dependencies are missing. Run: "
                "python -m pip install google-api-python-client google-auth"
            ) from exc

        # dotenv values are sometimes written with surrounding quotes on
        # Windows.  Treat those quotes as configuration syntax, not as part
        # of the filesystem path.
        raw = settings.GOOGLE_SHEETS_CREDENTIALS_JSON.strip().strip('"\'')
        if raw.startswith("{"):
            credentials = Credentials.from_service_account_info(
                json.loads(raw),
                scopes=["https://www.googleapis.com/auth/spreadsheets"],
            )
        else:
            credential_path = Path(raw)
            if not credential_path.is_file():
                raise RuntimeError(
                    "GOOGLE_SHEETS_CREDENTIALS_JSON must point to a "
                    "service-account .json file, not a directory."
                )
            credentials = Credentials.from_service_account_file(
                str(credential_path),
                scopes=["https://www.googleapis.com/auth/spreadsheets"],
            )
        return build("sheets", "v4", credentials=credentials, cache_discovery=False)

    @staticmethod
    def _lead_values(context: ToolContext, lead: Any) -> list[str]:
        return [
            str(getattr(lead, "id", "")),
            str(context.organization_id),
            str(context.conversation_id or ""),
            str(getattr(lead, "name", "") or ""),
            str(getattr(lead, "phone", "") or ""),
            str(getattr(lead, "email", "") or ""),
            str(getattr(lead, "interest", "") or ""),
            str(getattr(lead, "preferred_mode", "") or ""),
            str(getattr(lead, "preferred_time", "") or ""),
            str(getattr(lead, "notes", "") or ""),
            str(getattr(lead, "status", "") or ""),
            datetime.now(timezone.utc).isoformat(),
        ]

    def _upsert_sync(self, values: list[str]) -> dict[str, Any]:
        service = self._build_service()
        api = service.spreadsheets().values()
        sheet_range = settings.GOOGLE_SHEET_RANGE
        sheet_name = sheet_range.split("!", 1)[0]

        existing = api.get(
            spreadsheetId=settings.GOOGLE_SHEET_ID,
            range=sheet_range,
        ).execute().get("values", [])

        if not existing:
            api.update(
                spreadsheetId=settings.GOOGLE_SHEET_ID,
                range=f"{sheet_name}!A1:L1",
                valueInputOption="RAW",
                body={"values": [self.headers]},
            ).execute()
            existing = [self.headers]

        # Existing rows use columns B and C as the organization/conversation
        # key. A missing conversation is never upserted over another row.
        target_row: int | None = None
        for index, row in enumerate(existing[1:], start=2):
            if len(row) >= 3 and row[1] == values[1] and row[2] == values[2] and values[2]:
                target_row = index
                break

        if target_row is None:
            result = api.append(
                spreadsheetId=settings.GOOGLE_SHEET_ID,
                range=f"{sheet_name}!A:L",
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body={"values": [values]},
            ).execute()
            return {"operation": "append", "updated_range": result.get("updates", {}).get("updatedRange", "")}

        updated_range = f"{sheet_name}!A{target_row}:L{target_row}"
        api.update(
            spreadsheetId=settings.GOOGLE_SHEET_ID,
            range=updated_range,
            valueInputOption="USER_ENTERED",
            body={"values": [values]},
        ).execute()
        return {"operation": "update", "updated_range": updated_range}

    async def execute(
        self,
        context: ToolContext,
        arguments: dict[str, Any] | None = None,
    ) -> ToolResult:
        configuration_error = self._configuration_error()
        if configuration_error:
            return ToolResult(self.name, False, "Google Sheets sync is not configured.", error=configuration_error)

        lead = context.metadata.get("lead") if context.metadata else None
        if lead is None:
            return ToolResult(self.name, False, "A persisted lead is required before syncing.", error="lead_missing")

        try:
            values = self._lead_values(context, lead)
            result = await asyncio.to_thread(self._upsert_sync, values)
            return ToolResult(self.name, True, "Lead synced to Google Sheets.", data=result)
        except Exception as exc:
            return ToolResult(self.name, False, "Google Sheets sync failed.", error=str(exc))


class UnconfiguredIntegrationTool(BaseTool):
    def __init__(self, name: str, description: str, setup_hint: str) -> None:
        self.name = name
        self.description = description
        self.setup_hint = setup_hint
        self.requires_confirmation = True

    @property
    def input_schema(self) -> dict[str, Any]:
        return {"type": "object", "properties": {"payload": {"type": "object"}}, "additionalProperties": True}

    async def execute(self, context: ToolContext, arguments: dict[str, Any] | None = None) -> ToolResult:
        return ToolResult(self.name, False, f"{self.name} is recognized but not configured.", error=self.setup_hint)


def default_integration_tools() -> list[BaseTool]:
    return [
        GoogleSheetTool(),
        CRMSyncTool(),
        UnconfiguredIntegrationTool("send_email", "Send an email notification to the organization or customer.", "Configure an email provider and verified sender."),
        UnconfiguredIntegrationTool("send_whatsapp", "Send a WhatsApp message to a customer or organization contact.", "Configure WhatsApp Business API credentials and a phone number."),
        UnconfiguredIntegrationTool("book_appointment", "Create an appointment using the organization's calendar.", "Configure a calendar provider and availability rules."),
    ]
