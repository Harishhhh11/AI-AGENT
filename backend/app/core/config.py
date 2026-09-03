"""
Application configuration.

The application uses Ollama locally by default. Provider-related
settings are explicit so the runtime, diagnostics, and LLM factory all
use the same configuration names.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from backend/.env and environment variables."""

    APP_NAME: str = "AI Receptionist Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    HOST: str = "127.0.0.1"
    PORT: int = 8000

    DATABASE_URL: str
    SECRET_KEY: str

    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # LLM provider configuration.
    LLM_PROVIDER: str = "ollama"
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    OLLAMA_HOST: str = "http://127.0.0.1:11434"
    MODEL_NAME: str = "qwen2.5:3b"

    # Reserved for future OpenAI/compatible providers. Never commit a key.
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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

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


settings = Settings()
