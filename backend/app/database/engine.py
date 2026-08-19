"""
PostgreSQL database engine.
"""

from sqlalchemy import create_engine

from app.config.settings import settings


engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)