"""
Application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config.settings import settings


app = FastAPI(
    title="AI Receptionist Platform",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# API ROUTES
# ============================================================

app.include_router(
    api_router,
    prefix="/api/v1",
)


@app.get(
    "/",
)
def root():
    """
    Root endpoint.
    """

    return {
        "message": "AI Receptionist Platform API",
        "status": "running",
    }


@app.get(
    "/health",
)
def health():
    """
    Health check endpoint.
    """

    return {
        "status": "healthy",
    }
