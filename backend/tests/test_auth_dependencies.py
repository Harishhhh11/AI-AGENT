from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.auth import dependencies


class FakeQuery:
    def __init__(self, user):
        self.user = user

    def filter(self, *_args, **_kwargs):
        return self

    def first(self):
        return self.user


class FakeDB:
    def __init__(self, user):
        self.user = user

    def query(self, _model):
        return FakeQuery(self.user)


def _credentials():
    return SimpleNamespace(credentials="valid-token")


def test_inactive_organization_is_rejected(monkeypatch):
    organization = SimpleNamespace(is_active=False)
    user = SimpleNamespace(
        id=1,
        is_active=True,
        organization=organization,
    )

    monkeypatch.setattr(
        dependencies,
        "decode_access_token",
        lambda _token: {"user_id": 1},
    )

    with pytest.raises(HTTPException) as exc:
        dependencies.get_current_user(
            credentials=_credentials(),
            db=FakeDB(user),
        )

    assert exc.value.status_code == 403


def test_inactive_user_is_rejected(monkeypatch):
    organization = SimpleNamespace(is_active=True)
    user = SimpleNamespace(
        id=1,
        is_active=False,
        organization=organization,
    )

    monkeypatch.setattr(
        dependencies,
        "decode_access_token",
        lambda _token: {"user_id": 1},
    )

    with pytest.raises(HTTPException) as exc:
        dependencies.get_current_user(
            credentials=_credentials(),
            db=FakeDB(user),
        )

    assert exc.value.status_code == 403


def test_active_user_and_organization_are_accepted(monkeypatch):
    organization = SimpleNamespace(is_active=True)
    user = SimpleNamespace(
        id=1,
        is_active=True,
        organization=organization,
    )

    monkeypatch.setattr(
        dependencies,
        "decode_access_token",
        lambda _token: {"user_id": 1},
    )

    result = dependencies.get_current_user(
        credentials=_credentials(),
        db=FakeDB(user),
    )

    assert result is user
