"""
Tenant resolver.

Resolves the authenticated user's organization
and creates a TenantContext for protected APIs.
"""

from fastapi import Depends

from app.auth.dependencies import get_current_user
from app.models.user import User
from app.tenants.tenant_context import TenantContext


def get_current_tenant(
    current_user: User = Depends(
        get_current_user
    ),
) -> TenantContext:
    """
    Resolve the current tenant from the
    authenticated User object.
    """

    if current_user is None:
        raise ValueError(
            "Authenticated user was not found."
        )

    if current_user.id is None:
        raise ValueError(
            "Authenticated user has no user ID."
        )

    if current_user.organization_id is None:
        raise ValueError(
            "Authenticated user has no organization."
        )

    return TenantContext(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
    )