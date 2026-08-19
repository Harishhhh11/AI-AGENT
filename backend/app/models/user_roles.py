"""
User-Role association table.
"""

from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Table

from app.database.base import Base


user_roles = Table(
    "user_roles",
    Base.metadata,
    Column(
        "user_id",
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    ),
    Column(
        "role_id",
        ForeignKey(
            "roles.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    ),
)