"""Application entry point."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.router import api_router
from app.config.settings import settings
from app.database.session import SessionLocal
from app.middleware.request_context import RequestContextMiddleware


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
)


if settings.ACCESS_LOG_ENABLED:
    app.add_middleware(RequestContextMiddleware)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)


if settings.SECURE_HEADERS_ENABLED:

    @app.middleware("http")
    async def security_headers(request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=()"
        if settings.ENVIRONMENT in {"production", "prod"}:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "message": "AI Receptionist Platform API",
        "status": "running",
    }


@app.get("/health")
def health():
    """Liveness probe that does not require external dependencies."""
    return {"status": "healthy"}


@app.get("/ready")
def ready():
    """Readiness probe that verifies the primary database connection."""
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "dependencies": {"database": "unavailable"}},
        )
    finally:
        db.close()

    return {
        "status": "ready",
        "dependencies": {"database": "available"},
    }
