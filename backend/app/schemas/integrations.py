"""Integration catalog schemas."""

from pydantic import BaseModel


class IntegrationSummary(BaseModel):
    key: str
    name: str
    category: str
    description: str
    status: str
    setup_hint: str
    capabilities: list[str]


class IntegrationCatalog(BaseModel):
    integrations: list[IntegrationSummary]
