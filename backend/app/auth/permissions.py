"""Authorization helpers for organization-scoped APIs."""

from collections.abc import Iterable

from app.models.user import User


class Permission:
    """Canonical permission names used by protected APIs."""

    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"

    ROLE_CREATE = "role:create"
    ROLE_READ = "role:read"
    ROLE_UPDATE = "role:update"
    ROLE_DELETE = "role:delete"

    ORGANIZATION_READ = "organization:read"
    ORGANIZATION_UPDATE = "organization:update"

    AGENT_CREATE = "agent:create"
    AGENT_READ = "agent:read"
    AGENT_UPDATE = "agent:update"
    AGENT_DELETE = "agent:delete"


def get_user_permissions(user: User) -> set[str]:
    """Return the effective permissions granted through the user's roles."""

    permissions: set[str] = set()

    for role in user.roles or []:
        for permission in role.permissions or []:
            name = getattr(permission, "name", None)
            if name:
                permissions.add(name)

    return permissions


def has_permission(
    user_permissions: Iterable[str],
    permission: str,
) -> bool:
    """Return True when the requested permission is present."""

    return permission in set(user_permissions)


def require_permission(user: User, permission: str) -> None:
    """Raise PermissionError when the user lacks a required permission."""

    if user.is_superuser:
        return

    if not has_permission(
        get_user_permissions(user),
        permission,
    ):
        raise PermissionError(
            f"Missing required permission: {permission}"
        )
