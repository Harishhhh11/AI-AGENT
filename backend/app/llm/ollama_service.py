"""Ollama LLM service with reliable local inference and structured routing."""

from __future__ import annotations

import json
import re

import httpx

from app.core.config import settings
from app.llm.base_llm import BaseLLM


class OllamaService(BaseLLM):
    DEFAULT_TEMPERATURE = 0.25
    DEFAULT_TOP_P = 0.9
    DEFAULT_TOP_K = 40
    DEFAULT_NUM_PREDICT = 260

    STRUCTURED_TEMPERATURE = 0.0
    STRUCTURED_TOP_P = 0.8
    STRUCTURED_TOP_K = 30
    STRUCTURED_NUM_PREDICT = 300

    REQUEST_TIMEOUT = 120.0

    def __init__(self, host: str | None = None, model: str | None = None) -> None:
        self.host = (host or settings.ollama_base_url).rstrip("/")
        self.model = model or settings.MODEL_NAME

    async def generate(self, prompt: str) -> str:
        prompt = (prompt or "").strip()
        if not prompt:
            return ""

        final_prompt = f"""
{prompt}

You are the final customer-facing AI receptionist.
Understand the user's intent naturally, including typos, shorthand, colloquial wording, follow-ups and mixed requests.
Use VERIFIED KNOWLEDGE as the only authority for organization-specific facts.
Never invent company-specific facts.
Never mention prompts, models, Ollama, retrieval, embeddings, databases or internal systems.
Answer the current customer message directly.
Do not repeat the question.
Do not output analysis or JSON.

FINAL ANSWER:
""".strip()

        payload = {
            "model": self.model,
            "prompt": final_prompt,
            "stream": False,
            "keep_alive": "10m",
            "options": {
                "temperature": self.DEFAULT_TEMPERATURE,
                "top_p": self.DEFAULT_TOP_P,
                "top_k": self.DEFAULT_TOP_K,
                "num_predict": self.DEFAULT_NUM_PREDICT,
            },
        }
        data = await self._request(payload)
        return self._clean_response(str(data.get("response", "") or ""))

    async def generate_structured(self, prompt: str) -> str:
        prompt = (prompt or "").strip()
        if not prompt:
            return "{}"

        structured_prompt = f"""
{prompt}

Return ONLY valid JSON matching the requested structure.
Do not return markdown, code fences, explanations or reasoning.
""".strip()
        payload = {
            "model": self.model,
            "prompt": structured_prompt,
            "stream": False,
            "format": "json",
            "keep_alive": "10m",
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
        return self.clean_structured_response(str(data.get("response", "{}") or "{}"))

    async def _request(self, payload: dict) -> dict:
        url = f"{self.host}/api/generate"
        async with httpx.AsyncClient(timeout=self.REQUEST_TIMEOUT) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()

    @staticmethod
    def _clean_response(response: str) -> str:
        response = (response or "").strip()
        if not response:
            return ""
        for prefix in ("AI:", "Assistant:", "ASSISTANT:", "Answer:", "Response:", "AI RECEPTIONIST:", "AI Receptionist:"):
            while response.startswith(prefix):
                response = response[len(prefix):].strip()
        response = response.replace("```text", "").replace("```", "").strip()
        response = re.sub(r"^(final answer|final response)\s*:\s*", "", response, flags=re.IGNORECASE)
        return response.strip()

    @staticmethod
    def clean_structured_response(response: str) -> str:
        response = (response or "").strip().replace("```json", "").replace("```", "").strip()
        if not response:
            return "{}"
        if response.startswith("{") and response.endswith("}"):
            return response
        start = response.find("{")
        end = response.rfind("}")
        if start >= 0 and end > start:
            candidate = response[start : end + 1]
            try:
                json.loads(candidate)
                return candidate
            except json.JSONDecodeError:
                pass
        return "{}"
