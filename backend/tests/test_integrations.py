from app.services.integration_service import IntegrationService


def test_catalog_lists_selected_phase10_integrations_without_secrets():
    catalog = IntegrationService().catalog()
    keys = {item.key for item in catalog.integrations}
    assert keys == {"whatsapp", "voice", "crm", "email", "google_sheets"}
    assert all("key" not in item.description.lower() for item in catalog.integrations)


def test_catalog_reports_unconfigured_optional_integrations():
    catalog = IntegrationService().catalog()
    statuses = {item.key: item.status for item in catalog.integrations}
    assert statuses["crm"] == "available"
    assert statuses["google_sheets"] == "available"
