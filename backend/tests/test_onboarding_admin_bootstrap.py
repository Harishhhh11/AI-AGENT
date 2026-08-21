"""Regression tests for organization-admin bootstrap."""

from types import SimpleNamespace

from app.auth.bootstrap import (
    ADMIN_ROLE_NAME,
    bootstrap_organization_admin,
)


def test_bootstrap_assigns_organization_admin_role():
    permission_names = [
        "user:create",
        "user:read",
        "agent:read",
    ]

    role = SimpleNamespace(
        name=ADMIN_ROLE_NAME,
        permissions=[SimpleNamespace(name=name) for name in permission_names],
    )
    role.permissions = [
        SimpleNamespace(name="user:create"),
        SimpleNamespace(name="agent:update"),
    ]
    user = SimpleNamespace(
        organization_id=42,
        roles=[],
    )

    class FakeDB:
        def scalar(self, _statement):
            return role

        def add(self, _value):
            return None

        def flush(self):
            return None

    # This test intentionally focuses on the attach behavior without
    # requiring a live database. The repository/bootstrap integration test
    # remains responsible for exercising SQLAlchemy persistence.
    result = bootstrap_organization_admin(FakeDB(), user)

    assert result is role
    assert user.roles == [role]
