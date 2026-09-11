import pytest

from app.config.settings import Settings


def test_development_defaults_are_safe() -> None:
    settings = Settings(
        _env_file=None,
        DATABASE_URL="sqlite:///./test.db",
        SECRET_KEY="test-secret",
    )

    assert settings.DEBUG is False
    assert settings.llm_provider == "ollama"
    assert settings.ollama_base_url == "http://127.0.0.1:11434"


def test_production_rejects_weak_secret() -> None:
    with pytest.raises(ValueError, match="SECRET_KEY"):
        Settings(
            _env_file=None,
            ENVIRONMENT="production",
            SECRET_KEY="too-short",
            DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost/app",
            CORS_ALLOWED_ORIGINS="https://example.com",
        )


def test_production_rejects_debug() -> None:
    with pytest.raises(ValueError, match="DEBUG"):
        Settings(
            _env_file=None,
            ENVIRONMENT="production",
            DEBUG=True,
            SECRET_KEY="x" * 64,
            DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost/app",
            CORS_ALLOWED_ORIGINS="https://example.com",
        )


def test_production_rejects_sqlite() -> None:
    with pytest.raises(ValueError, match="SQLite"):
        Settings(
            _env_file=None,
            ENVIRONMENT="production",
            SECRET_KEY="x" * 64,
            DATABASE_URL="sqlite:///./production.db",
            CORS_ALLOWED_ORIGINS="https://example.com",
        )


def test_production_rejects_wildcard_cors() -> None:
    with pytest.raises(ValueError, match="Wildcard CORS"):
        Settings(
            _env_file=None,
            ENVIRONMENT="production",
            SECRET_KEY="x" * 64,
            DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost/app",
            CORS_ALLOWED_ORIGINS="*",
        )
