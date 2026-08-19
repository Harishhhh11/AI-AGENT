"""
Knowledge base schemas.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from pydantic import ConfigDict


class KnowledgeCreate(BaseModel):
    """
    Schema used when creating a knowledge record.
    """

    title: str

    content: str

    source: str

    category: str

    # Omit this to make a record available to every receptionist in the
    # organization. Supply an owned agent ID for agent-only knowledge.
    agent_id: int | None = None


class KnowledgeUpdate(BaseModel):
    """
    Schema used when updating a knowledge record.
    """

    title: str | None = None

    content: str | None = None

    source: str | None = None

    category: str | None = None

    is_active: bool | None = None


class KnowledgeResponse(BaseModel):
    """
    Schema returned by the knowledge API.
    """

    model_config = ConfigDict(
        from_attributes=True
    )

    id: int

    organization_id: int

    agent_id: int | None

    title: str

    content: str

    source: str

    category: str

    embedding: list[float] | None = None

    uuid: UUID

    is_active: bool

    created_at: datetime

    updated_at: datetime
