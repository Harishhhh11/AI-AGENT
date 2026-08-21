"""Default role and permission bootstrap helpers."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.permissions import Permission
from app.models.permission import Permission as PermissionModel
from app.models.role import Role
from app.models.user import User


DEFAULT_PERMISSIONS: tuple[tuple[str, str], ...] = (
    (Permission.USER_CREATE, "Create organization users."),
    (Permission.USER_READ, "Read organization users."),
    (Permission.USER_UPDATE, "Update organization users."),
    (Permission.USER_DELETE, "Delete organization users."),
    (Permission.ROLE_CREATE, "Create organization roles."),
    (Permission.ROLE_READ, "Read organization roles."),
    (Permission.ROLE_UPDATE, "Update organization roles."),
    (Permission.ROLE_DELETE, "Delete organization roles."),
    (Permission.ORGANIZATION_READ, "Read organization settings."),
    (Permission.ORGANIZATION_UPDATE, "Update organization settings."),
    (Permission.AGENT_CREATE, "Create AI agents."),
    (Permission.AGENT_READ, "Read AI agents."),
    (Permission.AGENT_UPDATE, "Update and publish AI agents."),
    (Permission.AGENT_DELETE, "Delete AI agents."),
)


ADMIN_ROLE_NAME = "organization_admin"


def ensure_default_permissions(db: Session) -> dict[str, PermissionModel]:
    """Create missing canonical permissions and return them by name."""

    permissions: dict[str, PermissionModel] = {}

    for name, description in DEFAULT_PERMISSIONS:
        permission = db.scalar(
            select(PermissionModel).where(PermissionModel.name == name)
        )
        if permission is None:
            permission = PermissionModel(
                name=name,
                description=description,
            )
            db.add(permission)
            db.flush()
        permissions[name] = permission

    return permissions


def ensure_organization_admin_role(
    db: Session,
    organization_id: int,
) -> Role:
    """Create/update the default organization administrator role."""

    role = db.scalar(
        select(Role)
        .where(Role.organization_id == organization_id)
        .where(Role.name == ADMIN_ROLE_NAME)
    )

    if role is None:
        role = Role(
            organization_id=organization_id,
            name=ADMIN_ROLE_NAME,
            description="Full administrative access within this organization.",
        )
        db.add(role)
        db.flush()

    permissions = ensure_default_permissions(db)
    role.permissions = list(permissions.values())

    return role


def bootstrap_organization_admin(
    db: Session,
    user: User,
) -> Role:
    """Attach the default admin role to the first organization user."""

    role = ensure_organization_admin_role(
        db,
        user.organization_id,
    )

    if role not in user.roles:
        user.roles.append(role)

    return role
