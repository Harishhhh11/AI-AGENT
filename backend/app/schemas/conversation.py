"""
Conversation schemas.
"""

from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict


class ConversationResponse(BaseModel):
    """
    Conversation API response.
    """

    model_config = ConfigDict(
        from_attributes=True
    )

    id: int

    organization_id: int

    agent_id: int | None

    user_id: int | None

    session_id: str

    status: str

    created_at: datetime

    updated_at: datetime


class ConversationStatusUpdate(BaseModel):
    """
    Update conversation status.
    """

    status: str


class MessageResponse(BaseModel):
    """
    Conversation message response.
    """

    model_config = ConfigDict(
        from_attributes=True
    )

    id: int

    conversation_id: int

    role: str

    content: str

    created_at: datetime
