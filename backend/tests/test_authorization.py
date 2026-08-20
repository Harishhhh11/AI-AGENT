from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.auth.authorization import require_permission
from app.auth.permissions import Permission, get_user_permissions


def test_permission_constants_include_agent_access() -> None:
    assert Permission.AGENT_CREATE == "agent:create"
    assert Permission.AGENT_READ == "agent:read"
    assert Permission.AGENT_UPDATE == "agent:update"
    assert Permission.AGENT_DELETE == "agent:delete"


def test_get_user_permissions_uses_roles_and_permissions() -> None:
    user = SimpleNamespace(
        roles=[
            SimpleNamespace(
                permissions=[
                    SimpleNamespace(name="agent:read"),
                    SimpleNamespace(name="agent:update"),
                ]
            ),
            SimpleNamespace(
                permissions=[
                    SimpleNamespace(name="organization:read"),
                ]
            ),
        ]
    )

    assert get_user_permissions(user) == {
        "agent:read",
        "agent:update",
        "organization:read",
    }


def test_require_permission_allows_superuser() -> None:
    dependency = require_permission("agent:delete")
    user = SimpleNamespace(
        is_superuser=True,
        roles=[],
    )

    assert dependency(current_user=user) is user


def test_require_permission_rejects_missing_permission() -> None:
    dependency = require_permission("agent:update")
    user = SimpleNamespace(
        is_superuser=False,
        roles=[
            SimpleNamespace(
                permissions=[
                    SimpleNamespace(name="agent:read"),
                ]
            )
        ],
    )

    with pytest.raises(HTTPException) as exc_info:
        dependency(current_user=user)

    assert exc_info.value.status_code == 403
