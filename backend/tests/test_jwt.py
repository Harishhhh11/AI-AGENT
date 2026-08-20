from datetime import timedelta

from jose import JWTError

from app.auth.jwt import create_access_token, decode_access_token


def test_access_token_round_trip() -> None:
    token = create_access_token(
        {
            "user_id": 123,
            "email": "user@example.com",
        }
    )

    payload = decode_access_token(token)

    assert payload["user_id"] == 123
    assert payload["email"] == "user@example.com"
    assert "exp" in payload


def test_expired_token_is_rejected() -> None:
    token = create_access_token(
        {"user_id": 123},
        expires_minutes=-1,
    )

    try:
        decode_access_token(token)
    except JWTError:
        return

    raise AssertionError("Expired token was accepted")
