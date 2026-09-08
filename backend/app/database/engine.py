"""
PostgreSQL database engine.
"""

from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy import event

from app.config.settings import settings


engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)


if settings.DATABASE_URL.lower().startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def register_sqlite_compatibility_functions(dbapi_connection, _connection_record):
        dbapi_connection.create_function(
            "now",
            0,
            lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        )