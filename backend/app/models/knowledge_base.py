"""
Knowledge base database model.
"""

from sqlalchemy import Boolean
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from pgvector.sqlalchemy import Vector

from app.database.base import Base
from app.models.base_model import BaseModel


class KnowledgeBase(Base, BaseModel):
    """
    Stores company knowledge and its vector embedding.
    """

    __tablename__ = "knowledge_base"

    organization_id: Mapped[int] = mapped_column(
        ForeignKey(
            "organizations.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # NULL means organization-wide shared knowledge.  A populated value
    # restricts the item to that receptionist only.
    agent_id: Mapped[int | None] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(384),
        nullable=True,
    )

    uuid: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        default=lambda: __import__("uuid").uuid4(),
        nullable=False,
        unique=True,
        index=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    agent = relationship("Agent", back_populates="knowledge_items")
