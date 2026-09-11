"""Answer synthesis from verified, tenant-scoped knowledge."""

from __future__ import annotations

import re


class KnowledgeAnswerService:
    """Extract concise requested facts without leaking source-document noise."""

    FACT_LABELS = {
        "fee": {"fee", "fees", "price", "pricing", "cost", "costs", "tuition"},
        "discount": {"discount", "discounts", "concession", "reduction", "offer"},
        "duration": {"duration", "length", "months", "weeks", "days"},
        "timings": {"timing", "timings", "schedule", "batch", "morning", "evening", "start"},
        "mode": {"online", "offline", "classroom", "mode", "remote", "remotely", "virtual"},
        "contact": {"phone", "mobile", "email", "address", "location", "contact"},
        "certificate": {"certificate", "certification", "completion"},
        "payment": {"payment", "pay", "installment", "installments", "paid", "full", "advance"},
        "eligibility": {"eligibility", "eligible", "requirement", "requirements", "required", "who can join"},
    }

    SUPPORTING_DETAIL_TERMS = {
        "available", "availability", "installment", "installments", "include", "includes", "included",
        "eligibility", "requirement", "requirements", "required", "benefit", "benefits", "certificate",
        "certification", "placement", "placements", "discount", "discounts", "offer", "offers",
        "registration", "admission", "admissions", "batch", "batches", "weekday", "weekend",
    }

    FIELD_PATTERNS = {
        "fee": (
            r"(?P<label>(?:the\s+)?(?:course\s*)?fee(?:s)?)\s*[:\-]\s*(?P<value>[^.\n]+)",
            r"(?P<label>(?:the\s+)?(?:course\s*)?fee(?:s)?)\s+(?P<verb>is|are)\s+(?P<value>[^.\n]+)",
            r"(?P<label>(?:the\s+)?(?:course\s*)?(?:price|pricing|cost|tuition))\s*[:\-]\s*(?P<value>[^.\n]+)",
            r"(?P<label>(?:the\s+)?(?:course\s*)?(?:price|pricing|cost|tuition))\s+(?P<verb>is|are)\s+(?P<value>[^.\n]+)",
        ),
        "duration": (
            r"(?P<label>duration)\s*[:\-]\s*(?P<value>[^.\n]+)",
            r"(?P<label>duration)\s+(?P<verb>is|of)\s+(?P<value>[^.\n]+)",
        ),
        "timings": (
            r"(?P<label>(?:class\s+)?schedule)\s*[:\-]\s*(?P<value>[^.\n]+)",
            r"(?P<label>(?:class\s+)?timings?)\s*[:\-]\s*(?P<value>[^.\n]+)",
            r"(?P<label>(?:class\s+)?timings?)\s+(?P<verb>are|is)\s+(?P<value>[^.\n]+)",
        ),
        "mode": (
            r"(?P<label>training\s+mode)\s*[:\-]\s*(?P<value>[^.\n]+)",
            r"(?P<label>mode)\s*[:\-]\s*(?P<value>[^.\n]+)",
            r"(?P<label>mode)\s+(?P<verb>is)\s+(?P<value>[^.\n]+)",
        ),
        "contact": (
            r"(?P<label>contact)\s*[:\-]\s*(?P<value>[^.\n]+)",
            r"(?P<label>(?:phone|mobile|email|address|location))\s*[:\-]\s*(?P<value>[^.\n]+)",
        ),
    }

    def answer(self, *, items: list[object], intent: str, subject: str | None, response_style: str) -> str | None:
        if not items:
            return None
        if intent in self.FACT_LABELS:
            return self._fact_answer(items, intent)
        if intent == "duration_and_timings":
            return self._join_answers(self._fact_answer(items, "duration"), self._fact_answer(items, "timings"))
        if intent in {"company_courses", "availability"}:
            return self._course_catalog(items)
        if intent == "topics":
            return self._topics_answer(items)
        if intent == "details" or response_style == "long":
            return self._summary(items, response_style)
        return None

    def _fact_answer(self, items: list[object], field: str) -> str | None:
        answers: list[str] = []
        seen_facts: set[str] = set()
        labels = self.FACT_LABELS[field]
        for item in items:
            title = self._clean_title(getattr(item, "title", ""))
            content = self._clean_preserve_lines(getattr(item, "content", ""))
            if not content:
                continue
            source_fact = self._source_fact_sentence(content, field)
            if source_fact:
                key = self._fact_key(source_fact)
                if key and key not in seen_facts:
                    seen_facts.add(key)
                    answers.append(self._with_title(title, source_fact))
                continue
            for piece in self._pieces(content):
                if not self._contains_fact(piece, labels):
                    continue
                key = self._fact_key(piece)
                if key and key not in seen_facts:
                    seen_facts.add(key)
                    answers.append(self._with_title(title, piece))
                break
            if len(answers) >= 4:
                break
        return " ".join(answers) if answers else None

    @classmethod
    def _source_fact_sentence(cls, content: str, field: str) -> str | None:
        for piece in cls._pieces(content):
            if not cls._contains_fact(piece, cls.FACT_LABELS[field]):
                continue
            extracted = cls._extract_field(piece, field)
            if extracted:
                return extracted
        return None

    @classmethod
    def _extract_field(cls, content: str, field: str) -> str | None:
        for pattern in cls.FIELD_PATTERNS.get(field, ()):
            match = re.search(pattern, content, flags=re.IGNORECASE)
            if not match:
                continue
            label = cls._clean(match.groupdict().get("label", ""))
            value = cls._clean(match.groupdict().get("value", "")).strip(" \t:-")
            if not value:
                continue
            verb = match.groupdict().get("verb")
            if verb:
                return f"{label} {verb} {value}.".replace("  ", " ")
            return f"{label}: {value}." if field in {"fee", "timings", "duration", "mode"} else f"{label} {value}."
        return None

    @classmethod
    def _topics_answer(cls, items: list[object]) -> str | None:
        results: list[str] = []
        seen: set[str] = set()
        for item in items:
            title = cls._clean_title(getattr(item, "title", ""))
            content = cls._clean_preserve_lines(getattr(item, "content", ""))
            pieces = cls._pieces(content)
            for index, piece in enumerate(pieces):
                match = re.search(r"(?:topics?|syllabus|curriculum|content)\s*[:\-]\s*(.+)", piece, re.IGNORECASE)
                if match:
                    candidate = match.group(1).strip(" .")
                    key = cls._fact_key(candidate)
                    if key and key not in seen:
                        seen.add(key)
                        results.append(cls._with_title(title, candidate))
                    continue
                if cls._looks_like_topic_sentence(piece):
                    key = cls._fact_key(piece)
                    if key and key not in seen:
                        seen.add(key)
                        results.append(cls._with_title(title, piece))
                if len(results) >= 8:
                    break
            if len(results) >= 8:
                break
        return " ".join(results) if results else None

    @staticmethod
    def _looks_like_topic_sentence(piece: str) -> bool:
        lower = piece.lower()
        return any(token in lower for token in (
            "variables", "variable", "functions", "function", "oop", "object-oriented", "inheritance",
            "polymorphism", "encapsulation", "abstraction", "arrays", "strings", "collections", "exception handling",
            "jdbc", "mysql", "spring boot", "rest api", "api", "database", "sql", "excel", "power bi",
            "machine learning", "data analysis", "programming", "project development",
        ))

    @classmethod
    def _course_catalog(cls, items: list[object]) -> str | None:
        names: list[str] = []
        seen: set[str] = set()
        for item in items:
            title = cls._clean_title(getattr(item, "title", ""))
            if title and not cls._generic_title(title):
                key = title.lower()
                if key not in seen:
                    seen.add(key)
                    names.append(title)
        return "We currently offer: " + ", ".join(names) + "." if names else None

    @staticmethod
    def _generic_title(title: str) -> bool:
        return bool(re.search(r"^(?:company|knowledge|faq|general|uploaded|document)\b", title, re.IGNORECASE))

    @staticmethod
    def _summary(items: list[object], response_style: str) -> str | None:
        max_chars = 1500 if response_style != "long" else 2200
        blocks: list[str] = []
        used = 0
        for item in items[:6]:
            title = KnowledgeAnswerService._clean_title(getattr(item, "title", ""))
            content = KnowledgeAnswerService._clean_preserve_lines(getattr(item, "content", ""))
            if not content:
                continue
            block = KnowledgeAnswerService._with_title(title, content)
            remaining = max_chars - used
            if remaining <= 0:
                break
            blocks.append(block[:remaining].rstrip())
            used += len(blocks[-1]) + 1
        return " ".join(blocks) if blocks else None

    @staticmethod
    def _with_title(title: str, content: str) -> str:
        if not title:
            return content.strip()
        return f"{title}: {content.strip()}"

    @staticmethod
    def _clean_title(value: object) -> str:
        text = re.sub(r"\s+", " ", str(value or "")).strip(" :-")
        text = re.sub(r"^(?:JAVA|PYTHON)\s+PROGRAMMING\s+COURSE\s*[:\-]\s*", "", text, flags=re.IGNORECASE)
        return text

    @staticmethod
    def _fact_key(value: str) -> str:
        text = re.sub(r"^[^:]+:\s*", "", KnowledgeAnswerService._clean(value)).lower()
        return re.sub(r"\s+", " ", text).strip(".")

    @staticmethod
    def _contains_fact(text: str, labels: set[str]) -> bool:
        normalized = str(text or "").lower()
        return any(re.search(rf"(?<![a-z0-9+#]){re.escape(label)}(?![a-z0-9+#])", normalized) for label in labels)

    @staticmethod
    def _pieces(text: str) -> list[str]:
        return [part.strip(" •\t") for part in re.split(r"(?<=[.!?])\s+|\r?\n+|\s+(?=•\s+)|\s+(?=-\s+)", text) if part.strip()]

    @staticmethod
    def _clean(value: object) -> str:
        return re.sub(r"\s+", " ", str(value or "")).strip()

    @staticmethod
    def _clean_preserve_lines(value: object) -> str:
        return re.sub(r"[ \t]+", " ", str(value or "")).strip()

    @staticmethod
    def _join_answers(first: str | None, second: str | None) -> str | None:
        values = [v for v in (first, second) if v]
        return " ".join(values) if values else None
