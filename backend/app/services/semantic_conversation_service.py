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
    """Fast Ollama-assisted semantic routing with deterministic safety fallback."""

    ALLOWED_INTENTS = {
        "general", "company_courses", "topics", "fee", "discount", "duration", "timings",
        "duration_and_timings", "mode", "admission", "contact", "company_information", "details",
        "availability", "certificate", "payment", "eligibility", "lead", "unknown",
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
            result = self._normalize_result(data, message)
            return result if result and result.questions else None
        except Exception as exc:
            print("Semantic conversation analysis error:", exc)
            return None

    def fallback(self, message: str, conversation_context: str = "") -> SemanticConversation:
        parts = self._split_questions(message)
        questions = [self._fallback_question(part) for part in parts] or [self._fallback_question(message)]
        intents = [q["intent"] for q in questions]
        intent = intents[0] if len(set(intents)) == 1 else "multi_part"
        subject = questions[0].get("subject") if len(questions) == 1 else None
        style = "medium" if len(questions) > 1 or intent in {"topics", "details", "company_courses", "multi_part"} else "short"
        requires_knowledge = any(q["intent"] not in {"general", "lead", "unknown"} for q in questions)
        wants_lead = any(q["intent"] == "lead" for q in questions) or any(x in self._normalize(message) for x in ("contact me", "call me", "book a demo", "sign me up"))
        return SemanticConversation(intent, subject, questions[:6], style, requires_knowledge, wants_lead)

    def _fallback_question(self, message: str) -> dict:
        normalized = self._normalize(message)
        intent = self._detect_intent(normalized)
        subject = self._fallback_subject(normalized)
        return {"text": message.strip(), "intent": intent, "subject": subject}

    def _detect_intent(self, normalized: str) -> str:
        if not normalized:
            return "unknown"
        if re.search(r"\b(?:certificate|certification|completion)\b", normalized):
            return "certificate"
        if re.search(r"\b(?:payment|pay|installment|installments)\b", normalized):
            return "payment"
        if re.search(r"\b(?:how much|fee|fees|price|pricing|cost|tuition)\b", normalized):
            return "fee"
        if re.search(r"\b(?:duration|how long|length|months?|weeks?|days?)\b", normalized):
            return "duration"
        if re.search(r"\b(?:timing|timings|schedule|batch|class time|when is the class)\b", normalized):
            return "timings"
        if re.search(r"\b(?:topic|topics|syllabus|curriculum|covered|cover|content)\b", normalized):
            return "topics"
        if re.search(r"\b(?:online|offline|classroom|remote|virtual)\b", normalized):
            return "mode"
        if re.search(r"\b(?:eligibility|eligible|requirements?|who can join)\b", normalized):
            return "eligibility"
        if re.search(r"\b(?:contact|phone|mobile|email|address|location)\b", normalized):
            return "contact"
        if re.search(r"\b(?:join|enroll|enrol|register|admission|sign up)\b", normalized):
            return "admission"
        if re.search(r"\b(?:which|what)\s+(?:courses?|programs?|training)\b|\bwhat do you offer\b", normalized):
            return "company_courses"
        return "general"

    def _build_prompt(self, message: str, context: str, available_subjects: list[str]) -> str:
        subjects = ", ".join(dict.fromkeys(s.strip() for s in available_subjects if s.strip()))[:1800]
        return f"""
You are the semantic routing engine for an AI receptionist.
Understand meaning, spelling mistakes, shorthand, colloquial phrasing and conversational context.
Never invent company facts. You only classify and route; verified knowledge is supplied separately.
Resolve elliptical follow-ups from the conversation, such as "what's the fee?" after discussing Java.
Detect every independent request in a single message and preserve the original wording in each question.
Choose a subject from the known knowledge titles when it is the closest semantic match.
Do not use words like what, whats, how, provide, pay, tell, please as subjects.

Allowed intents: {', '.join(sorted(self.ALLOWED_INTENTS))}
Known knowledge subjects/titles:
{subjects or '(none)'}

Conversation context:
{context or '(none)'}

Customer message:
{message}

Return only JSON:
{{
  "intent": "one allowed intent",
  "subject": "canonical subject/title or null",
  "questions": [
    {{"text": "original independent request", "intent": "one allowed intent", "subject": "canonical subject/title or null"}}
  ],
  "response_style": "short|medium|long",
  "requires_knowledge": true,
  "wants_lead_action": false
}}
""".strip()

    def _normalize_result(self, data: dict, message: str) -> SemanticConversation | None:
        if not isinstance(data, dict):
            return None
        intent = self._normalize_intent(data.get("intent"))
        subject = self._clean_subject(data.get("subject"))
        questions: list[dict] = []
        raw_questions = data.get("questions")
        if isinstance(raw_questions, list):
            for raw in raw_questions[:6]:
                if not isinstance(raw, dict):
                    continue
                text = str(raw.get("text") or "").strip()
                if not text:
                    continue
                questions.append({
                    "text": text,
                    "intent": self._normalize_intent(raw.get("intent") or intent),
                    "subject": self._clean_subject(raw.get("subject")) or subject,
                })
        if not questions:
            questions = [{"text": message.strip(), "intent": intent, "subject": subject}]
        style = str(data.get("response_style") or "short").lower()
        if style not in {"short", "medium", "long"}:
            style = "short"
        return SemanticConversation(
            intent=intent,
            subject=subject,
            questions=questions,
            response_style=style,
            requires_knowledge=bool(data.get("requires_knowledge")),
            wants_lead_action=bool(data.get("wants_lead_action")),
        )

    def _normalize_intent(self, value) -> str:
        intent = str(value or "unknown").strip().lower()
        return intent if intent in self.ALLOWED_INTENTS else "unknown"

    @staticmethod
    def _clean_subject(value) -> str | None:
        if value is None:
            return None
        text = re.sub(r"\s+", " ", str(value).strip(" \t\n\r\"'"))
        if not text or text.lower() in {"null", "none", "unknown", "n/a"}:
            return None
        if text.lower() in {"what", "whats", "what's", "how", "provide", "pay", "tell", "please"}:
            return None
        return text[:120]

    @staticmethod
    def _fallback_subject(normalized: str) -> str | None:
        patterns = (
            r"(?:fee|fees|price|pricing|cost|tuition|duration|timings?|schedule|topics?|syllabus|curriculum|mode|certificate|payment|eligibility)\s+(?:for|of|in|on)\s+([a-z][a-z0-9+# ._-]{1,80})$",
            r"(?:for|about)\s+(?:the\s+)?([a-z][a-z0-9+# ._-]{1,80})$",
        )
        for pattern in patterns:
            match = re.search(pattern, normalized)
            if match:
                value = re.sub(r"\s+", " ", match.group(1)).strip(" ?.!")
                if value not in {"what", "whats", "how", "provide", "pay", "tell"}:
                    return value
        return None

    @staticmethod
    def _split_questions(message: str) -> list[str]:
        text = (message or "").strip()
        if not text:
            return []
        pieces = []
        for part in re.split(r"\?(?:\s+|$)", text):
            part = part.strip()
            if not part:
                continue
            if not part.endswith("?"):
                part = part + "?"
            pieces.append(part)
        return pieces

    @staticmethod
    def _normalize(value: str) -> str:
        return " ".join(str(value or "").lower().replace("’", "'").split()).strip(" ?!.,;:")
