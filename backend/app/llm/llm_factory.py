"""LLM provider factory."""

from app.core.config import settings
from app.llm.base_llm import BaseLLM
from app.llm.ollama_service import OllamaService


def get_llm() -> BaseLLM:
    """Return the configured LLM implementation.

    Ollama is the supported local provider for the current project.
    The provider name is normalized so missing configuration safely
    defaults to Ollama instead of producing a connection-less client.
    """

    provider = settings.llm_provider

    if provider in {"ollama", "local", ""}:
        return OllamaService()

    raise ValueError(
        f"Unsupported LLM_PROVIDER={provider!r}. "
        "Use LLM_PROVIDER=ollama for the local Ollama setup."
    )
