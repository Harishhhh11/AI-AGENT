"""
Authentication schemas.
"""

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    organization_id: int
    first_name: str
    last_name: str
    email: EmailStr
    phone: str | None = None
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: int
    email: EmailStr