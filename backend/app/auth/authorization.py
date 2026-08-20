"""FastAPI dependencies for permission-based authorization."""

from collections.abc import Callable

from fastapi import Depends, HTTPException, status

from app.auth.dependencies import get_current_user
from app.auth.permissions import get_user_permissions
from app.models.user import User


def require_permission(permission: str) -> Callable:
    """Create a FastAPI dependency requiring one permission."""

    def dependency(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.is_superuser:
            return current_user

        permissions = get_user_permissions(current_user)
        if permission not in permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )

        return current_user

    return dependency
