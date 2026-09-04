"""
Lead schemas.
"""

import re

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator


_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PHONE_RE = re.compile(r"^\+?[0-9][0-9\s().-]{5,24}$")


class LeadCreate(BaseModel):

    name: str | None = Field(default=None, max_length=150)

    phone: str | None = Field(default=None, max_length=50)

    email: str | None = Field(default=None, max_length=255)

    interest: str | None = Field(default=None, max_length=255)

    preferred_mode: str | None = Field(default=None, max_length=100)

    preferred_time: str | None = Field(default=None, max_length=100)

    notes: str | None = Field(default=None, max_length=10000)

    @field_validator(
        "name",
        "phone",
        "email",
        "interest",
        "preferred_mode",
        "preferred_time",
        "notes",
        mode="before",
    )
    @classmethod
    def strip_strings(cls, value):
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("Lead fields must be strings.")
        value = value.strip()
        return value or None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value):
        if value is not None and (
            not _PHONE_RE.fullmatch(value)
            or len(re.sub(r"\D", "", value)) < 7
            or len(re.sub(r"\D", "", value)) > 15
        ):
            raise ValueError("Phone must contain 7 to 15 digits.")
        return value

    @field_validator("email")
    @classmethod
    def validate_email(cls, value):
        if value is not None and not _EMAIL_RE.fullmatch(value):
            raise ValueError("Email must be a valid email address.")
        return value.lower() if value else value


class LeadUpdate(LeadCreate):
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