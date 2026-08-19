"""
Base interface for LLM providers.

Supports:

- Normal customer-facing text generation
- Structured JSON generation for internal application tasks
"""

from abc import ABC, abstractmethod


class BaseLLM(ABC):
    """
    Base interface for all LLM providers.
    """

    @abstractmethod
    async def generate(
        self,
        prompt: str,
    ) -> str:
        """
        Generate normal customer-facing text.
        """
        raise NotImplementedError

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
    ) -> str:
        """
        Generate structured output for internal operations.

        Examples:
        - Lead extraction
        - Classification
        - Structured data extraction
        """
        raise NotImplementedError