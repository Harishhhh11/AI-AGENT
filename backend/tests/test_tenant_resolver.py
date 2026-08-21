from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.tenants.resolver import get_current_tenant


class FakeQuery:
    def __init__(self, organization):
        self.organization = organization

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self.organization


class FakeDB:
    def __init__(self, organization):
        self.organization = organization

    def query(self, model):
        return FakeQuery(self.organization)


def test_current_tenant_resolves_active_organization() -> None:
    user = SimpleNamespace(
        id=7,
        organization_id=42,
    )
    organization = SimpleNamespace(
        id=42,
        is_active=True,
    )

    context = get_current_tenant(
        current_user=user,
        db=FakeDB(organization),
    )

    assert context.organization_id == 42
    assert context.user_id == 7


def test_current_tenant_rejects_missing_organization() -> None:
    user = SimpleNamespace(
        id=7,
        organization_id=42,
    )

    with pytest.raises(HTTPException) as exc_info:
        get_current_tenant(
            current_user=user,
            db=FakeDB(None),
        )

    assert exc_info.value.status_code == 403


def test_current_tenant_rejects_inactive_organization() -> None:
    user = SimpleNamespace(
        id=7,
        organization_id=42,
    )
    organization = SimpleNamespace(
        id=42,
        is_active=False,
    )

    with pytest.raises(HTTPException) as exc_info:
        get_current_tenant(
            current_user=user,
            db=FakeDB(organization),
        )

    assert exc_info.value.status_code == 403


def test_current_tenant_rejects_user_without_organization() -> None:
    user = SimpleNamespace(
        id=7,
        organization_id=None,
    )

    with pytest.raises(HTTPException) as exc_info:
        get_current_tenant(
            current_user=user,
            db=FakeDB(None),
        )

    assert exc_info.value.status_code == 403
