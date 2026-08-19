"""
Permission utilities.
"""


class Permission:

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
    AGENT_UPDATE = "agent:update"
    AGENT_DELETE = "agent:delete"


def has_permission(
    user_permissions: list[str],
    permission: str,
) -> bool:

    return permission in user_permissions