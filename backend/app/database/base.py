"""
Declarative Base.

Every database model inherits from Base.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass