"""Schemas for organization-scoped roles and permissions."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RoleCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=255)
    permission_names: list[str] = Field(default_factory=list)


class RoleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=255)
    permission_names: list[str] | None = None


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    uuid: UUID
    organization_id: int
    name: str
    description: str | None
    permissions: list[str]
    created_at: datetime
    updated_at: datetime
