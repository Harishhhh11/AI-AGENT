"""Application entry point."""

from __future__ import annotations

from collections import Counter
from time import monotonic

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
_started_at = monotonic()
_request_counts: Counter[str] = Counter()


if settings.ACCESS_LOG_ENABLED:
    app.add_middleware(RequestContextMiddleware)


@app.middleware("http")
async def request_metrics(request, call_next):
    response = await call_next(request)
    _request_counts[f"{request.method} {request.url.path} {response.status_code}"] += 1
    return response


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


@app.get("/metrics", include_in_schema=False)
def metrics():
    """Expose minimal scrape-compatible process metrics without sensitive data."""
    lines = [
        "# HELP app_uptime_seconds Process uptime in seconds.",
        "# TYPE app_uptime_seconds gauge",
        f"app_uptime_seconds {monotonic() - _started_at:.3f}",
        "# HELP app_http_requests_total HTTP responses by method, path, and status.",
        "# TYPE app_http_requests_total counter",
    ]
    for labels, count in sorted(_request_counts.items()):
        method, path, status = labels.split(" ", 2)
        lines.append(
            f'app_http_requests_total{{method="{method}",path="{path}",status="{status}"}} {count}'
        )
    return "\n".join(lines) + "\n"
