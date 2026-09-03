"""Application settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


_PLACEHOLDER_SECRET = "CHANGE_THIS_TO_A_LONG_RANDOM_SECRET_KEY"


class Settings(BaseSettings):
    """Runtime configuration with explicit provider settings."""

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
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    DATABASE_URL: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/ai_receptionist"
    )

    SECRET_KEY: str = Field(default=_PLACEHOLDER_SECRET)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Local LLM defaults.
    LLM_PROVIDER: str = "ollama"
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    OLLAMA_HOST: str = "http://127.0.0.1:11434"
    MODEL_NAME: str = "qwen2.5:3b"
    OPENAI_API_KEY: str = ""
    LLM_BASE_URL: str = ""

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

    CORS_ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    SECURE_HEADERS_ENABLED: bool = True
    ACCESS_LOG_ENABLED: bool = True

    @property
    def cors_allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()]

    @property
    def llm_provider(self) -> str:
        return (self.LLM_PROVIDER or "ollama").strip().lower()

    @property
    def ollama_base_url(self) -> str:
        return (
            self.OLLAMA_BASE_URL
            or self.OLLAMA_HOST
            or "http://127.0.0.1:11434"
        ).rstrip("/")

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
