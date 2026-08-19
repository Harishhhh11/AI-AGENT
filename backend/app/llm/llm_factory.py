"""
LLM factory.
"""

from app.llm.base_llm import BaseLLM
from app.llm.ollama_service import OllamaService


def get_llm() -> BaseLLM:

    return OllamaService()