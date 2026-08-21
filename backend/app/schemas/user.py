"""
User schemas.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import EmailStr


class UserBase(BaseModel):

    first_name: str
    last_name: str
    email: EmailStr
    phone: str | None = None


class UserCreate(UserBase):

    organization_id: int
    password: str


class UserUpdate(BaseModel):

    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    is_active: bool | None = None
    is_verified: bool | None = None


class UserRoleUpdate(BaseModel):
    """Request to add or remove an organization role."""

    role_id: int


class UserResponse(UserBase):

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    uuid: UUID

    organization_id: int

    is_active: bool
    is_verified: bool
    is_superuser: bool

    role_ids: list[int] = []

    created_at: datetime
    updated_at: datetime
