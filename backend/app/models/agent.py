"""Configurable AI receptionist owned by an organization."""

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.base_model import BaseModel


class Agent(Base, BaseModel):
    """A publishable AI receptionist.

    An organization may own several agents, for example Sales, Support,
    and Admissions.  ``public_slug`` is deliberately global and stable so
    it can safely be used in a customer-facing URL or website widget.
    """

    __tablename__ = "agents"

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(150), nullable=False)

    public_slug: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )

    welcome_message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="Hello! How can I help you today?",
    )

    system_instructions: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    is_published: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    organization = relationship("Organization", back_populates="agents")
    conversations = relationship("Conversation", back_populates="agent")
    knowledge_items = relationship("KnowledgeBase", back_populates="agent")
