"""Chat request and response schemas."""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request body for an AI receptionist conversation."""

    message: str = Field(min_length=1, max_length=5000)
    session_id: str | None = Field(default=None, max_length=100)
    agent_id: int | None = Field(default=None, ge=1)


class ChatResponse(BaseModel):
    """Response returned by an AI receptionist."""

    session_id: str
    response: str
