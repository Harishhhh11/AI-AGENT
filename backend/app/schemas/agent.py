"""Schemas for organization-owned AI receptionists."""

import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AgentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    public_slug: str = Field(min_length=3, max_length=100)
    welcome_message: str = Field(
        default="Hello! How can I help you today?", min_length=1, max_length=1000
    )
    system_instructions: str | None = Field(default=None, max_length=6000)

    @field_validator("public_slug")
    @classmethod
    def validate_public_slug(cls, value: str) -> str:
        slug = value.strip().lower()
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
            raise ValueError(
                "Public slug may contain lowercase letters, numbers, and hyphens only."
            )
        return slug


class AgentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    welcome_message: str | None = Field(default=None, min_length=1, max_length=1000)
    system_instructions: str | None = Field(default=None, max_length=6000)
    is_active: bool | None = None


class AgentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    uuid: UUID
    organization_id: int
    name: str
    public_slug: str
    welcome_message: str
    is_published: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PublicAgentResponse(BaseModel):
    """Safe configuration intentionally exposed to anonymous customers."""

    model_config = ConfigDict(from_attributes=True)

    name: str
    public_slug: str
    welcome_message: str
