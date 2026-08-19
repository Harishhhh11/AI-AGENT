"""
Chat request and response schemas.
"""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """
    Request body for the AI receptionist.
    """

    message: str = Field(
        min_length=1,
        max_length=5000,
    )

    session_id: str | None = Field(
        default=None,
        max_length=100,
    )


class ChatResponse(BaseModel):
    """
    Response returned by the AI receptionist.
    """

    session_id: str

    response: str