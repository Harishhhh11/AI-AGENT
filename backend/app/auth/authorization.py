"""FastAPI dependencies for permission-based authorization."""

from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.permissions import get_user_permissions
from app.database.session import get_db
from app.models.role import Role
from app.models.user import User


def require_permission(permission: str) -> Callable:
    """Create a FastAPI dependency requiring one permission."""

    def dependency(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        if current_user.is_superuser:
            return current_user

        # Always resolve roles from the current database session.
        # This prevents authorization from depending on a stale or
        # partially-loaded current_user.roles relationship.
        roles = (
            db.query(Role)
            .join(Role.users)
            .filter(
                User.id == current_user.id,
                Role.organization_id == current_user.organization_id,
            )
            .all()
        )

        permissions: set[str] = set()

        for role in roles:
            for role_permission in role.permissions or []:
                name = getattr(role_permission, "name", None)
                if name:
                    permissions.add(name)

        # Compatibility fallback for callers/tests that populate the
        # user's ORM relationships directly.
        if not permissions:
            permissions = get_user_permissions(current_user)

        if permission not in permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )

        return current_user

    return dependency
