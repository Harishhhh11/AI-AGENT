from __future__ import annotations

import json
import re
from dataclasses import dataclass

from app.llm.base_llm import BaseLLM


@dataclass
class SemanticConversation:
    intent: str
    subject: str | None
    questions: list[dict]
    response_style: str
    requires_knowledge: bool
    wants_lead_action: bool


class SemanticConversationService:
    """Ollama-assisted language understanding with a deterministic fallback."""

    ALLOWED_INTENTS = {
        "general", "company_courses", "topics", "fee", "discount", "duration",
        "timings", "duration_and_timings", "mode", "admission", "contact",
        "company_information", "details", "availability", "lead", "unknown",
    }

    FALLBACK_INTENT_MARKERS = {
        "fee": ("fee", "fees", "price", "pricing", "cost", "tuition", "payment", "pay"),
        "timings": ("timing", "timings", "schedule", "batch", "class time", "when is the class"),
        "duration": ("duration", "how long", "length", "months", "weeks", "days"),
        "topics": ("topic", "topics", "syllabus", "curriculum", "covered", "cover", "content"),
        "mode": ("online", "offline", "classroom", "remote", "virtual"),
        "contact": ("contact", "phone", "mobile", "email", "address", "location"),
        "certificate": ("certificate", "certification", "completion certificate"),
        "admission": ("join", "enroll", "enrol", "register", "admission", "sign up"),
        "company_courses": ("what do you offer", "which courses", "what courses", "courses available"),
    }

    def __init__(self, llm: BaseLLM | None):
        self.llm = llm

    async def analyze(self, message: str, conversation_context: str, available_subjects: list[str] | None = None) -> SemanticConversation | None:
        if not self.llm:
            return None
        prompt = self._build_prompt(message, conversation_context, available_subjects or [])
        try:
            raw = await self.llm.generate_structured(prompt)
            data = json.loads(raw)
            normalized = self._normalize_result(data, message)
            if normalized:
                return normalized
        except Exception as exc:
            print("Semantic conversation analysis error:", exc)
        return None

    def fallback(self, message: str, conversation_context: str = "") -> SemanticConversation:
        normalized = self._normalize(message)
        intent = "general"
        for candidate, markers in self.FALLBACK_INTENT_MARKERS.items():
            if any(marker in normalized for marker in markers):
                intent = candidate
                break
        subject = self._fallback_subject(message)
        questions = [{"text": part.strip(), "intent": intent, "subject": subject} for part in self._split_questions(message) if part.strip()]
        if not questions:
            questions = [{"text": message.strip(), "intent": intent, "subject": subject}]
        response_style = "medium" if len(questions) > 1 or intent in {"topics", "details", "duration_and_timings"} else "short"
        requires_knowledge = intent not in {"general", "lead"}
        wants_lead_action = intent == "lead" or any(token in normalized for token in ("contact me", "call me", "book", "register", "sign me up"))
        return SemanticConversation(intent, subject, questions, response_style, requires_knowledge, wants_lead_action)

    def _build_prompt(self, message: str, context: str, available_subjects: list[str]) -> str:
        subjects = ", ".join(dict.fromkeys(s.strip() for s in available_subjects if s.strip()))[:1500]
        return f"""
You are the semantic conversation router for an AI receptionist.
Understand the customer's meaning, not exact keywords.
Normalize minor spelling mistakes and colloquial phrasing.
Use the conversation context to resolve missing subjects such as 'what's the fee?' after a Java discussion.
Detect every independent question in a multi-question message.
Never invent a company fact. This output only classifies the request and identifies what knowledge should be retrieved.

Allowed intents: {', '.join(sorted(self.ALLOWED_INTENTS))}

Known knowledge subjects/titles:
{subjects or '(unknown)'}

Conversation context:
{context or '(none)'}

Customer message:
{message}

Return JSON only with this exact shape:
{{
  "intent": "one allowed intent",
  "subject": "course/product/service subject or null",
  "questions": [
    {{"text": "original sub-question", "intent": "one allowed intent", "subject": "subject or null"}}
  ],
  "response_style": "short|medium|long",
  "requires_knowledge": true,
  "wants_lead_action": false
}}
""".strip()

    def _normalize_result(self, data: dict, message: str) -> SemanticConversation | None:
        if not isinstance(data, dict):
            return None
        intent = str(data.get("intent") or "unknown").strip().lower()
        if intent not in self.ALLOWED_INTENTS:
            intent = "unknown"
        subject = self._clean_subject(data.get("subject"))
        raw_questions = data.get("questions")
        questions = []
        if isinstance(raw_questions, list):
            for item in raw_questions:
                if not isinstance(item, dict):
                    continue
                text = str(item.get("text") or "").strip()
                q_intent = str(item.get("intent") or intent).strip().lower()
                if q_intent not in self.ALLOWED_INTENTS:
                    q_intent = intent
                q_subject = self._clean_subject(item.get("subject")) or subject
                if text:
                    questions.append({"text": text, "intent": q_intent, "subject": q_subject})
        if not questions:
            questions = [{"text": message.strip(), "intent": intent, "subject": subject}]
        style = str(data.get("response_style") or "short").lower()
        if style not in {"short", "medium", "long"}:
            style = "short"
        return SemanticConversation(
            intent=intent,
            subject=subject,
            questions=questions[:6],
            response_style=style,
            requires_knowledge=bool(data.get("requires_knowledge")),
            wants_lead_action=bool(data.get("wants_lead_action")),
        )

    @staticmethod
    def _clean_subject(value) -> str | None:
        if value is None:
            return None
        text = re.sub(r"\s+", " ", str(value).strip(" \t\n\r\"'"))
        if not text or text.lower() in {"null", "none", "unknown", "n/a"}:
            return None
        return text[:120]

    @classmethod
    def _fallback_subject(cls, message: str) -> str | None:
        normalized = cls._normalize(message)
        normalized = re.sub(r"^(?:what|what's|whats|which|can|could|would|do|does|did|is|are|please|tell me)\b\s*", "", normalized)
        patterns = (
            r"(?:fee|fees|price|pricing|cost|tuition|duration|timings?|schedule|topics?|syllabus|curriculum|mode|certificate)\s+(?:for|of)\s+(.+)",
            r"(?:for|about)\s+([a-z][a-z0-9+# ._-]{1,80})$",
        )
        for pattern in patterns:
            match = re.search(pattern, normalized)
            if match:
                return re.sub(r"\s+", " ", match.group(1)).strip(" ?.!")
        return None

    @staticmethod
    def _split_questions(message: str) -> list[str]:
        text = (message or "").replace("?", "?\n")
        return [chunk.strip() for chunk in text.splitlines() if chunk.strip()]

    @staticmethod
    def _normalize(value: str) -> str:
        return " ".join(str(value or "").lower().replace("’", "'").split()).strip(" ?!.,;:")
