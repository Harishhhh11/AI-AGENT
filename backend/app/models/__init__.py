"""
Import all database models and association tables.

This ensures SQLAlchemy knows about all tables and relationships
before the ORM is configured.
"""

from app.models.user_roles import user_roles
from app.models.role_permissions import role_permissions

from app.models.organization import Organization
from app.models.agent import Agent
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User

from app.models.conversation import Conversation
from app.models.message import Message
from app.models.lead import Lead
from app.models.knowledge_base import KnowledgeBase


__all__ = [
    "user_roles",
    "role_permissions",
    "Organization",
    "Agent",
    "Permission",
    "Role",
    "User",
    "Conversation",
    "Message",
    "Lead",
    "KnowledgeBase",
]
