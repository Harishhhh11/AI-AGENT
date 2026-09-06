"""Provider-neutral integration catalog and configuration status."""

from app.config.settings import settings
from app.schemas.integrations import IntegrationCatalog, IntegrationSummary


class IntegrationService:
    """Expose safe integration metadata without returning credentials."""

    def catalog(self) -> IntegrationCatalog:
        return IntegrationCatalog(
            integrations=[
                self._item(
                    "whatsapp", "WhatsApp", "Messaging",
                    "Receive and reply to customer messages through WhatsApp Business.",
                    "Configure a WhatsApp Business provider and verified phone number.",
                    ["inbound_messages", "outbound_messages"],
                    False,
                ),
                self._item(
                    "voice", "Voice", "Channels",
                    "Normalize voice transcripts and return receptionist responses.",
                    "Connect a voice provider and webhook adapter.",
                    ["inbound_calls", "outbound_responses"],
                    False,
                ),
                self._item(
                    "crm", "CRM", "Business systems",
                    "Sync qualified leads into the configured CRM pipeline.",
                    "Set CRM_ENABLED and CRM_WEBHOOK_URL.",
                    ["lead_sync"],
                    settings.CRM_ENABLED and bool(settings.CRM_WEBHOOK_URL),
                ),
                self._item(
                    "email", "Email", "Notifications",
                    "Send lead and conversation notifications to your team.",
                    "Configure an email provider and verified sender.",
                    ["notifications"],
                    False,
                ),
                self._item(
                    "google_sheets", "Google Sheets", "Business systems",
                    "Upsert captured leads into a shared spreadsheet.",
                    "Set GOOGLE_SHEETS_ENABLED, sheet ID, and service-account credentials.",
                    ["lead_sync"],
                    settings.GOOGLE_SHEETS_ENABLED
                    and bool(settings.GOOGLE_SHEET_ID)
                    and bool(settings.GOOGLE_SHEETS_CREDENTIALS_JSON),
                ),
            ]
        )

    @staticmethod
    def _item(
        key: str,
        name: str,
        category: str,
        description: str,
        setup_hint: str,
        capabilities: list[str],
        configured: bool,
    ) -> IntegrationSummary:
        return IntegrationSummary(
            key=key,
            name=name,
            category=category,
            description=description,
            status="configured" if configured else "available",
            setup_hint=setup_hint,
            capabilities=capabilities,
        )
