"""
Organization database model.
"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.database.base import Base
from app.models.base_model import BaseModel


class Organization(Base, BaseModel):
    """
    Organization table.
    """

    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    users = relationship(
        "User",
        back_populates="organization",
        cascade="all, delete-orphan",
    )

    agents = relationship(
        "Agent",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
