"""
Application configuration.
"""

from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):

    APP_NAME: str = "AI Receptionist Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    DATABASE_URL: str

    SECRET_KEY: str

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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
