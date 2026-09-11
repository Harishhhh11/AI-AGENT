from __future__ import annotations

import json
import re
from dataclasses import dataclass

from app.llm.base_llm import BaseLLM


@dataclass(frozen=True)
class SemanticQuestion:
    text: str
    intent: str
    subject: str | None


@dataclass(frozen=True)
class SemanticConversation:
    intent: str
    subject: str | None
    questions: list[dict]
    response_style: str
    requires_knowledge: bool
    wants_lead_action: bool


class SemanticConversationService:
    """Fast Ollama-assisted semantic routing with a conservative deterministic fallback."""

    ALLOWED_INTENTS = {
        "general", "company_courses", "topics", "fee", "discount", "duration",
        "timings", "duration_and_timings", "mode", "admission", "contact",
        "company_information", "details", "availability", "certificate", "payment",
        "eligibility", "lead", "unknown", "multi_part",
    }

    INTENT_HINTS = {
        "fee": "price, fee, cost, tuition, payment amount",
        "discount": "discount, offer, concession, reduction",
        "duration": "duration, length, months, weeks, days, how long",
        "timings": "timings, schedule, batch, class time, when classes happen",
        "topics": "topics, syllabus, curriculum, what is covered, course content",
        "mode": "online, offline, classroom, virtual, remote, delivery mode",
        "certificate": "certificate, certification, completion certificate",
        "payment": "pay, payment method, installment, installments, advance, full payment",
        "eligibility": "who can join, eligibility, requirements, qualifications",
        "admission": "join, enroll, register, admission, sign up",
        "contact": "contact, phone, mobile, email, address, location",
        "company_courses": "courses, programs, training, services, products the company offers",
        "details": "complete or detailed information",
    }

    FALLBACK_MARKERS = (
        ("duration", ("duration", "how long", "length", "months", "weeks", "days")),
        ("timings", ("timing", "timings", "schedule", "batch", "class time", "when is the class")),
        ("certificate", ("certificate", "certification", "completion certificate")),
        ("payment", ("payment", "pay", "installment", "installments", "advance", "full payment")),
        ("fee", ("fee", "fees", "price", "pricing", "cost", "tuition")),
        ("topics", ("topic", "topics", "syllabus", "curriculum", "covered", "cover", "content")),
        ("eligibility", ("eligible", "eligibility", "requirements", "qualification", "who can join")),
        ("mode", ("online", "offline", "classroom", "remote", "virtual")),
        ("contact", ("contact", "phone", "mobile", "email", "address", "location")),
        ("admission", ("join", "enroll", "enrol", "register", "admission", "sign up")),
        ("company_courses", ("what do you offer", "which courses", "what courses", "courses available")),
    )

    COMMON_TYPO_NORMALIZATIONS = {
        "whats": "what is",
        "whts": "what is",
        "wats": "what is",
        "hows": "how is",
        "complition": "completion",
        "certifcate": "certificate",
        "certification": "certificate",
        "timng": "timing",
        "timngs": "timings",
        "duraton": "duration",
        "durration": "duration",
        "pythonning": "python",
        "feeing": "fee",
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
            return self._normalize_result(data, message, available_subjects or [])
        except Exception as exc:
            print("Semantic conversation analysis error:", exc)
            return None

    def fallback(self, message: str, conversation_context: str = "", available_subjects: list[str] | None = None) -> SemanticConversation:
        available = [str(s).strip() for s in (available_subjects or []) if str(s).strip()]
        normalized = self._canonicalize(message)
        parts = self._split_questions(message)
        if not parts:
            parts = [message.strip()]
        previous_subject = self._subject_from_context(conversation_context, available)
        questions: list[dict] = []
        for part in parts[:8]:
            canonical = self._canonicalize(part)
            intent = self._detect_fallback_intent(canonical)
            subject = self._fallback_subject(canonical, available) or previous_subject
            questions.append({"text": part.strip(), "intent": intent, "subject": subject})
        first = questions[0] if questions else {"intent": "general", "subject": previous_subject}
        intent = first["intent"]
        subject = first.get("subject")
        if len(questions) > 1:
            intent = "multi_part"
        response_style = "medium" if len(questions) > 1 or intent in {"topics", "details", "duration_and_timings", "multi_part", "company_courses", "availability"} else "short"
        requires_knowledge = any(item["intent"] not in {"general", "lead", "unknown"} for item in questions)
        wants_lead_action = intent == "lead" or any(token in normalized for token in ("contact me", "call me", "book", "register", "sign me up"))
        return SemanticConversation(intent, subject, questions, response_style, requires_knowledge, wants_lead_action)

    def _build_prompt(self, message: str, context: str, available_subjects: list[str]) -> str:
        subjects = ", ".join(dict.fromkeys(s.strip() for s in available_subjects if s.strip()))[:2000]
        intent_lines = "\n".join(f"- {name}: {description}" for name, description in self.INTENT_HINTS.items())
        return f"""
You are the language-understanding engine for a production AI receptionist.
Your job is to understand what the customer means, not to answer the question.

Rules:
- Interpret spelling mistakes, shorthand, missing apostrophes, colloquial language and paraphrases.
- Resolve follow-ups from the conversation, e.g. after Java discussion, "whats the fee?" means Java fee.
- Detect every independent request in a mixed message.
- Match the customer's subject to the closest known knowledge subject when appropriate.
- Do not invent company facts.
- Never decide tenant identity, permissions, agent authorization, database identity, or lead-state authority.
- Return only the requested JSON structure.

Available intents:
{intent_lines}

Known knowledge subjects/titles:
{subjects or "(none provided)"}

Recent conversation:
{context or "(none)"}

Customer message:
{message}

Return JSON:
{{
  "intent": "one allowed intent; use multi_part when there are multiple independent requests",
  "subject": "best matching known subject or null",
  "questions": [
    {{"text": "original sub-question", "intent": "intent", "subject": "subject or null"}}
  ],
  "response_style": "short|medium|long",
  "requires_knowledge": true,
  "wants_lead_action": false
}}
""".strip()

    def _normalize_result(self, data: dict, message: str, available_subjects: list[str]) -> SemanticConversation:
        intent = str(data.get("intent") or "unknown").strip().lower()
        if intent not in self.ALLOWED_INTENTS:
            intent = "unknown"
        subject = self._canonical_subject(data.get("subject"), available_subjects)
        questions: list[dict] = []
        raw_questions = data.get("questions")
        if isinstance(raw_questions, list):
            for item in raw_questions:
                if not isinstance(item, dict):
                    continue
                text = str(item.get("text") or "").strip()
                q_intent = str(item.get("intent") or intent).strip().lower()
                if q_intent not in self.ALLOWED_INTENTS:
                    q_intent = intent
                q_subject = self._canonical_subject(item.get("subject"), available_subjects) or subject
                if text:
                    questions.append({"text": text, "intent": q_intent, "subject": q_subject})
        if not questions:
            questions = [{"text": message.strip(), "intent": intent, "subject": subject}]
        if len(questions) > 1 and intent not in {"multi_part", "unknown"}:
            intent = "multi_part"
        style = str(data.get("response_style") or "short").lower()
        if style not in {"short", "medium", "long"}:
            style = "medium" if len(questions) > 1 else "short"
        requires_knowledge = bool(data.get("requires_knowledge")) or any(
            q["intent"] not in {"general", "lead", "unknown"} for q in questions
        )
        return SemanticConversation(
            intent=intent,
            subject=subject,
            questions=questions[:8],
            response_style=style,
            requires_knowledge=requires_knowledge,
            wants_lead_action=bool(data.get("wants_lead_action")),
        )

    @classmethod
    def _canonical_subject(cls, value, available_subjects: list[str]) -> str | None:
        text = cls._clean_subject(value)
        if not text:
            return None
        if not available_subjects:
            return text
        normalized = cls._canonicalize(text)
        best = None
        best_score = 0.0
        for candidate in available_subjects:
            candidate = str(candidate or "").strip()
            if not candidate:
                continue
            score = cls._subject_similarity(normalized, cls._canonicalize(candidate))
            if score > best_score:
                best = candidate
                best_score = score
        return best if best_score >= 0.42 else text

    @classmethod
    def _fallback_subject(cls, message: str, available_subjects: list[str]) -> str | None:
        normalized = cls._canonicalize(message)
        available = [(cls._canonicalize(s), s) for s in available_subjects if str(s).strip()]
        for normalized_subject, original in available:
            short = re.sub(r"\s+(?:programming|course|training)$", "", normalized_subject).strip()
            aliases = {normalized_subject, short}
            if any(alias and re.search(rf"(?<![a-z0-9+#]){re.escape(alias)}(?![a-z0-9+#])", normalized) for alias in aliases):
                return original
        if len(available) == 1:
            return available[0][1]
        patterns = (
            r"(?:fee|fees|price|pricing|cost|tuition|duration|timings?|schedule|topics?|syllabus|curriculum|mode|certificate|payment|eligibility|requirements?)\s+(?:for|of)\s+([a-z][a-z0-9+# ._-]{1,80})$",
            r"(?:for|about)\s+([a-z][a-z0-9+# ._-]{1,80})$",
        )
        for pattern in patterns:
            match = re.search(pattern, normalized)
            if match:
                raw_subject = match.group(1).strip(" ?.!")
                return cls._canonical_subject(raw_subject, available_subjects)
        return None

    @classmethod
    def _detect_fallback_intent(cls, normalized: str) -> str:
        if any(marker in normalized for marker in ("what do you offer", "which courses", "what courses", "courses available")):
            return "company_courses"
        if any(marker in normalized for marker in ("certificate", "certification", "completion")):
            return "certificate"
        if any(marker in normalized for marker in ("payment", "pay", "installment", "installments", "advance")):
            return "payment"
        if any(marker in normalized for marker in ("who can join", "eligibility", "eligible", "requirements", "qualification")):
            return "eligibility"
        for candidate, markers in cls.FALLBACK_MARKERS:
            if any((marker in normalized) if " " in marker else (marker in normalized.split()) for marker in markers):
                return candidate
        return "general"

    @classmethod
    def _split_questions(cls, message: str) -> list[str]:
        text = (message or "").strip()
        if not text:
            return []
        # Question marks are authoritative boundaries when present.
        if "?" in text:
            pieces = [p.strip() for p in re.split(r"\?(?:\s+|$)", text) if p.strip()]
            return [p + "?" for p in pieces] if pieces else [text]
        # Never split a single sentence/question merely because it begins with a
        # common interrogative word. Only split at explicit connectors that introduce
        # another interrogative clause.
        parts = re.split(
            r"\s+(?=(?:and|also|plus)\s+(?:what|what's|whats|which|how|can|could|would|is|are|do|does|will|where|when|who|why)\b)",
            text,
            flags=re.IGNORECASE,
        )
        return [p.strip() for p in parts if p.strip()] or [text]

    @classmethod
    def _canonicalize(cls, value: str) -> str:
        text = str(value or "").lower().replace("’", "'")
        words = []
        for word in re.findall(r"[a-z0-9+#.'-]+", text):
            clean = word.strip(".'-")
            words.append(cls.COMMON_TYPO_NORMALIZATIONS.get(clean, clean))
        normalized = " ".join(words)
        return normalized.replace("what is is", "what is")

    @staticmethod
    def _clean_subject(value) -> str | None:
        if value is None:
            return None
        text = re.sub(r"\s+", " ", str(value).strip(" \t\n\r\"'"))
        if not text or text.lower() in {"null", "none", "unknown", "n/a"}:
            return None
        return text[:120]

    @classmethod
    def _subject_from_context(cls, context: str, available_subjects: list[str]) -> str | None:
        normalized = cls._canonicalize(context)
        for subject in available_subjects:
            subject_normalized = cls._canonicalize(subject)
            if subject_normalized and subject_normalized in normalized:
                return subject
            short = re.sub(r"\s+(?:programming|course|training)$", "", subject_normalized)
            if short and short in normalized:
                return subject
        return None

    @staticmethod
    def _subject_similarity(first: str, second: str) -> float:
        first_tokens = set(re.findall(r"[a-z0-9+#.-]+", first))
        second_tokens = set(re.findall(r"[a-z0-9+#.-]+", second))
        if not first_tokens or not second_tokens:
            return 0.0
        overlap = len(first_tokens & second_tokens) / len(first_tokens | second_tokens)
        if first in second or second in first:
            overlap += 0.45
        return min(1.0, overlap)
