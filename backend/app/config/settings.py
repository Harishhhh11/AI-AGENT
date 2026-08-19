"""
Application settings.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    APP_NAME: str = "AI Receptionist Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    DATABASE_URL: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/ai_receptionist"
    )

    SECRET_KEY: str = Field(
        default="CHANGE_THIS_TO_A_LONG_RANDOM_SECRET_KEY"
    )

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

    # Comma-separated frontend origins allowed to call the API. Public chat
    # is rendered inside a platform-controlled iframe, so customer websites
    # do not need broad API access.
    CORS_ALLOWED_ORIGINS: str = (
        "http://localhost:5173,http://127.0.0.1:5173"
    )

    @property
    def cors_allowed_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.CORS_ALLOWED_ORIGINS.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings():

    return Settings()


settings = get_settings()
