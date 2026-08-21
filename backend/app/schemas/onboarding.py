"""Schemas for company onboarding."""

from pydantic import BaseModel, EmailStr, Field


class OnboardingRequest(BaseModel):
    organization_name: str = Field(min_length=2, max_length=150)
    organization_email: EmailStr
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    admin_email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    phone: str | None = Field(default=None, max_length=20)
    agent_name: str = Field(default="AI Receptionist", min_length=2, max_length=150)
    public_slug: str = Field(min_length=3, max_length=100)


class OnboardingResponse(BaseModel):
    organization_id: int
    admin_user_id: int
    agent_id: int
    public_slug: str
