"""
Database session management.
"""

from collections.abc import Generator

from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

from app.database.engine import engine


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def get_db() -> Generator[Session, None, None]:
    """
    Provide a database session for each request.
    """

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()