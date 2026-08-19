"""
Lead schemas.
"""

from pydantic import BaseModel
from pydantic import ConfigDict


class LeadCreate(BaseModel):

    name: str | None = None

    phone: str | None = None

    email: str | None = None

    interest: str | None = None

    preferred_mode: str | None = None

    preferred_time: str | None = None

    notes: str | None = None


class LeadUpdate(BaseModel):

    name: str | None = None

    phone: str | None = None

    email: str | None = None

    interest: str | None = None

    preferred_mode: str | None = None

    preferred_time: str | None = None

    notes: str | None = None

    status: str | None = None


class LeadResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )

    id: int

    organization_id: int

    conversation_id: int | None

    name: str | None

    phone: str | None

    email: str | None

    interest: str | None

    preferred_mode: str | None

    preferred_time: str | None

    notes: str | None

    status: str