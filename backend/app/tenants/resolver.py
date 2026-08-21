"""
Tenant resolver.

Resolves the authenticated user's organization and creates a
TenantContext for protected APIs.
"""

from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models.organization import Organization
from app.models.user import User
from app.tenants.tenant_context import TenantContext


def get_current_tenant(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TenantContext:
    """
    Resolve the current tenant from the authenticated User.

    The organization is loaded again from the database so protected
    APIs do not rely only on a possibly stale ORM relationship or JWT
    claims. Inactive organizations are rejected centrally.
    """

    if current_user is None or current_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user was not found.",
        )

    organization_id = current_user.organization_id

    if organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with an organization.",
        )

    organization = (
        db.query(Organization)
        .filter(Organization.id == organization_id)
        .first()
    )

    if organization is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization not found.",
        )

    if not organization.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization is inactive.",
        )

    return TenantContext(
        organization_id=organization.id,
        user_id=current_user.id,
    )
