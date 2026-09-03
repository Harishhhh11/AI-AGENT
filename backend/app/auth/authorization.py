"""FastAPI dependencies for permission-based authorization."""

from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models.permission import Permission as PermissionModel
from app.models.role import Role
from app.models.user import User
from app.models.role_permissions import role_permissions
from app.models.user_roles import user_roles


ADMIN_ROLE_NAME = "organization_admin"


def require_permission(permission: str) -> Callable:
    """Create a FastAPI dependency requiring one organization permission."""

    def dependency(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        # Superusers bypass organization permission checks.
        if current_user.is_superuser:
            return current_user

        # The canonical organization_admin role is a full administrator.
        # Check the user's role membership directly from the database first.
        # This makes existing tenants resilient even if their permission
        # association rows were created before the RBAC bootstrap was added.
        admin_role_statement = (
            select(Role.id)
            .select_from(user_roles)
            .join(Role, Role.id == user_roles.c.role_id)
            .where(user_roles.c.user_id == current_user.id)
            .where(Role.organization_id == current_user.organization_id)
            .where(Role.name == ADMIN_ROLE_NAME)
        )

        if db.scalar(admin_role_statement) is not None:
            return current_user

        # Resolve normal permissions through the association tables.
        statement = (
            select(PermissionModel.name)
            .select_from(user_roles)
            .join(Role, Role.id == user_roles.c.role_id)
            .join(
                role_permissions,
                role_permissions.c.role_id == Role.id,
            )
            .join(
                PermissionModel,
                PermissionModel.id == role_permissions.c.permission_id,
            )
            .where(user_roles.c.user_id == current_user.id)
            .where(Role.organization_id == current_user.organization_id)
        )

        permissions = set(db.scalars(statement).all())

        if permission not in permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )

        return current_user

    return dependency
