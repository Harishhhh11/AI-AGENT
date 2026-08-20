from types import SimpleNamespace

import pytest

from app.auth.permissions import Permission, get_user_permissions, has_permission, require_permission


def test_get_user_permissions_collects_role_permissions() -> None:
    user = SimpleNamespace(
        is_superuser=False,
        roles=[
            SimpleNamespace(
                permissions=[
                    SimpleNamespace(name=Permission.AGENT_READ),
                    SimpleNamespace(name=Permission.AGENT_UPDATE),
                ]
            ),
            SimpleNamespace(
                permissions=[
                    SimpleNamespace(name=Permission.LEAD_READ)
                    if hasattr(Permission, "LEAD_READ")
                    else SimpleNamespace(name="lead:read")
                ]
            ),
        ],
    )

    permissions = get_user_permissions(user)

    assert Permission.AGENT_READ in permissions
    assert Permission.AGENT_UPDATE in permissions
    assert "lead:read" in permissions


def test_has_permission() -> None:
    assert has_permission(
        [Permission.AGENT_READ],
        Permission.AGENT_READ,
    )
    assert not has_permission(
        [Permission.AGENT_READ],
        Permission.AGENT_DELETE,
    )


def test_require_permission_allows_superuser() -> None:
    user = SimpleNamespace(
        is_superuser=True,
        roles=[],
    )

    require_permission(user, Permission.AGENT_DELETE)


def test_require_permission_rejects_missing_permission() -> None:
    user = SimpleNamespace(
        is_superuser=False,
        roles=[
            SimpleNamespace(
                permissions=[
                    SimpleNamespace(name=Permission.AGENT_READ),
                ]
            )
        ],
    )

    with pytest.raises(PermissionError):
        require_permission(user, Permission.AGENT_DELETE)
