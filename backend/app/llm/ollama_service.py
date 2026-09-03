"""
Ollama LLM service.

Provides a controlled interface to Ollama models.

Supports:

- Normal customer-facing generation
- Structured JSON generation
- Qwen / local inference
- Controlled temperature
- Controlled output length
"""

import json
import re

import httpx

from app.core.config import settings
from app.llm.base_llm import BaseLLM


class OllamaService(BaseLLM):
    """
    Ollama-backed LLM service.

    This class is completely company-agnostic.

    Company-specific behavior belongs in the application
    services and prompts.
    """

    DEFAULT_TEMPERATURE = 0.25
    DEFAULT_TOP_P = 0.9
    DEFAULT_TOP_K = 40
    DEFAULT_NUM_PREDICT = 180

    STRUCTURED_TEMPERATURE = 0.0
    STRUCTURED_TOP_P = 0.8
    STRUCTURED_TOP_K = 30
    STRUCTURED_NUM_PREDICT = 300

    REQUEST_TIMEOUT = 120.0

    def __init__(
        self,
        host: str | None = None,
        model: str | None = None,
    ) -> None:
        # IMPORTANT: use the canonical Ollama URL from config.
        # OLLAMA_BASE_URL is the primary setting, while
        # OLLAMA_HOST remains supported as a fallback.
        # This prevents local Python from accidentally using the
        # Docker-only host.docker.internal address.
        self.host = (
            host or settings.ollama_base_url
        ).rstrip("/")

        self.model = model or settings.MODEL_NAME

    async def generate(self, prompt: str) -> str:
        """Generate normal customer-facing text."""
        prompt = (prompt or "").strip()

        if not prompt:
            return ""

        final_prompt = f"""
{prompt}

============================================================
FINAL RESPONSE RULE
============================================================

Return ONLY the final answer to the customer's CURRENT
MESSAGE.

Do not repeat the customer's question.
Do not rewrite or paraphrase the customer's question.
Do not ask the customer's question back.
Do not output analysis.
Do not output reasoning.
Do not output instructions.
Do not output JSON.
Do not output labels such as:
AI:
Assistant:
Answer:
Response:

Answer the customer directly.

If the customer asks a simple question, give a short answer.

If the customer asks for several details, give only the
relevant details.

Use only verified company information supplied in the prompt.

If information is unavailable, say so honestly.

FINAL CUSTOMER-FACING ANSWER:
""".strip()

        payload = {
            "model": self.model,
            "prompt": final_prompt,
            "stream": False,
            "options": {
                "temperature": self.DEFAULT_TEMPERATURE,
                "top_p": self.DEFAULT_TOP_P,
                "top_k": self.DEFAULT_TOP_K,
                "num_predict": self.DEFAULT_NUM_PREDICT,
            },
        }

        data = await self._request(payload)
        generated = str(data.get("response", "") or "").strip()
        return self._clean_response(generated)

    async def generate_structured(self, prompt: str) -> str:
        """Generate structured internal output."""
        prompt = (prompt or "").strip()

        if not prompt:
            return "{}"

        structured_prompt = f"""
{prompt}

============================================================
STRUCTURED OUTPUT RULE
============================================================

Return ONLY valid JSON.

Do not output markdown.
Do not output ```json.
Do not output ```.
Do not output explanations.
Do not output reasoning.
Do not output conversational text.

The first character of your response must be {{.
The last character of your response must be }}.
""".strip()

        payload = {
            "model": self.model,
            "prompt": structured_prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": self.STRUCTURED_TEMPERATURE,
                "top_p": self.STRUCTURED_TOP_P,
                "top_k": self.STRUCTURED_TOP_K,
                "num_predict": self.STRUCTURED_NUM_PREDICT,
            },
        }

        try:
            data = await self._request(payload)
        except Exception:
            payload.pop("format", None)
            data = await self._request(payload)

        generated = data.get("response", "{}")
        return str(generated or "{}").strip()

    async def _request(self, payload: dict) -> dict:
        """Send a request to the configured Ollama server."""
        url = f"{self.host}/api/generate"

        async with httpx.AsyncClient(timeout=self.REQUEST_TIMEOUT) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()

    @staticmethod
    def _clean_response(response: str) -> str:
        """Clean common customer-facing model artifacts."""
        response = (response or "").strip()

        if not response:
            return ""

        prefixes = (
            "AI:",
            "Assistant:",
            "ASSISTANT:",
            "Answer:",
            "Response:",
            "AI RECEPTIONIST:",
            "AI Receptionist:",
        )

        changed = True
        while changed:
            changed = False
            for prefix in prefixes:
                if response.startswith(prefix):
                    response = response[len(prefix):].strip()
                    changed = True

        response = (
            response
            .replace("```text", "")
            .replace("```", "")
            .strip()
        )

        response = re.sub(
            r"^(final answer|final response)\s*:\s*",
            "",
            response,
            flags=re.IGNORECASE,
        )

        return response.strip()

    @staticmethod
    def clean_structured_response(response: str) -> str:
        """Extract the JSON object from a model response."""
        response = (response or "").strip()

        if not response:
            return "{}"

        response = (
            response
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )

        if response.startswith("{") and response.endswith("}"):
            return response

        start = response.find("{")
        end = response.rfind("}")

        if start >= 0 and end > start:
            candidate = response[start:end + 1]
            try:
                json.loads(candidate)
                return candidate
            except json.JSONDecodeError:
                pass

        return "{}"
