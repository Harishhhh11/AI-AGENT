"""
Permission database model.
"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.database.base import Base
from app.models.base_model import BaseModel


class Permission(Base, BaseModel):
    """
    Permission table.
    """

    __tablename__ = "permissions"

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    roles = relationship(
        "Role",
        secondary="role_permissions",
        back_populates="permissions",
    )