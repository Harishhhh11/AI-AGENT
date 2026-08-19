"""
Organization schemas.
"""

from pydantic import EmailStr
from pydantic import Field

from app.schemas.common import BaseSchema


class OrganizationCreate(BaseSchema):
    """
    Request schema.
    """

    name: str = Field(
        min_length=2,
        max_length=150,
    )

    email: EmailStr


class OrganizationResponse(BaseSchema):
    """
    Response schema.
    """

    id: int

    name: str

    email: EmailStr