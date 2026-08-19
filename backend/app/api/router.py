"""
Main API router.
"""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.agents import router as agents_router
from app.api.v1.chat import router as chat_router
from app.api.v1.conversations import (
    router as conversations_router,
)
from app.api.v1.documents import (
    router as documents_router,
)
from app.api.v1.knowledge import (
    router as knowledge_router,
)
from app.api.v1.leads import (
    router as leads_router,
)
from app.api.v1.organizations import (
    router as organization_router,
)
from app.api.v1.users import (
    router as user_router,
)


api_router = APIRouter()


# Authentication
api_router.include_router(
    auth_router,
)

api_router.include_router(
    agents_router,
)


# Chat
api_router.include_router(
    chat_router,
)


# Leads
api_router.include_router(
    leads_router,
)


# Conversations
api_router.include_router(
    conversations_router,
)


# Knowledge Base
api_router.include_router(
    knowledge_router,
)


# Documents
api_router.include_router(
    documents_router,
)


# Organizations
api_router.include_router(
    organization_router,
)


# Users
api_router.include_router(
    user_router,
)
