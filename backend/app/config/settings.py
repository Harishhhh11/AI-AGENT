"""Application settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


_PLACEHOLDER_SECRET = "CHANGE_THIS_TO_A_LONG_RANDOM_SECRET_KEY"


class Settings(BaseSettings):
    """Runtime configuration with explicit production safety checks."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    APP_NAME: str = "AI Receptionist Platform"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    DATABASE_URL: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/ai_receptionist"
    )

    SECRET_KEY: str = Field(default=_PLACEHOLDER_SECRET)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    OLLAMA_HOST: str = "http://localhost:11434"
    MODEL_NAME: str = "qwen2.5:3b"

    GOOGLE_SHEET_NAME: str = "AI Receptionist Leads"
    GOOGLE_SHEETS_ENABLED: bool = False
    GOOGLE_SHEET_ID: str = ""
    GOOGLE_SHEET_RANGE: str = "Leads!A:L"
    GOOGLE_SHEETS_CREDENTIALS_JSON: str = ""

    CRM_ENABLED: bool = False
    CRM_WEBHOOK_URL: str = ""
    CRM_API_KEY: str = ""
    CRM_PIPELINE: str = "Leads"
    CRM_STAGE: str = "new"
    CRM_TIMEOUT_SECONDS: int = 10

    # Comma-separated frontend origins allowed to call the API.
    CORS_ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    SECURE_HEADERS_ENABLED: bool = True
    ACCESS_LOG_ENABLED: bool = True

    @property
    def cors_allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()]

    @field_validator("ENVIRONMENT")
    @classmethod
    def normalize_environment(cls, value: str) -> str:
        return value.strip().lower()

    @model_validator(mode="after")
    def validate_production_safety(self) -> "Settings":
        if self.ENVIRONMENT in {"production", "prod"}:
            if self.DEBUG:
                raise ValueError("DEBUG must be false in production")
            if self.SECRET_KEY == _PLACEHOLDER_SECRET or len(self.SECRET_KEY) < 32:
                raise ValueError("SECRET_KEY must be a strong value of at least 32 characters in production")
            if not self.CORS_ALLOWED_ORIGINS.strip():
                raise ValueError("CORS_ALLOWED_ORIGINS must be explicitly configured in production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
