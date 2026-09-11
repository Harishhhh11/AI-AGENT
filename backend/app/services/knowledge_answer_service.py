"""Grounded response synthesis from tenant-scoped knowledge."""

from __future__ import annotations

import re


class KnowledgeAnswerService:
    """Extract concise answers from verified knowledge without hallucinating facts."""

    FACT_LABELS = {
        "fee": {"fee", "fees", "price", "pricing", "cost", "costs", "tuition"},
        "discount": {"discount", "discounts", "concession", "reduction", "offer"},
        "duration": {"duration", "length", "months", "weeks", "days"},
        "timings": {"timing", "timings", "schedule", "batch", "batches", "morning", "afternoon", "evening", "start"},
        "mode": {"online", "offline", "classroom", "mode", "remote", "remotely", "virtual"},
        "contact": {"phone", "mobile", "email", "address", "location", "contact"},
        "certificate": {"certificate", "certification", "completion"},
        "payment": {"payment", "pay", "installment", "installments", "paid", "full", "advance"},
        "eligibility": {"eligibility", "eligible", "requirement", "requirements", "required", "qualification", "qualifications", "who", "join"},
    }

    FIELD_PATTERNS = {
        "fee": (
            r"(?P<label>(?:the\s+)?(?:course\s*)?fees?)\s*[:\-]\s*(?P<value>[^.\n]+)",
            r"(?P<label>(?:fee|fees|price|pricing|cost|tuition))\s*(?:is|are)\s*[:\-]?\s*(?P<value>[^.\n]+)",
        ),
        "duration": (
            r"(?P<label>duration)\s*[:\-]\s*(?P<value>[^.\n]+)",
            r"(?P<label>course\s+length)\s*[:\-]\s*(?P<value>[^.\n]+)",
            r"(?P<label>duration)\s*(?:is|of)\s*[:\-]?\s*(?P<value>[^.\n]+)",
        ),
        "timings": (
            r"(?P<label>(?:batch\s+)?timings?)\s*[:\-]\s*(?P<value>[^.\n]+)",
            r"(?P<label>schedule)\s*[:\-]\s*(?P<value>[^.\n]+)",
            r"(?P<label>(?:class\s+)?time)\s*[:\-]\s*(?P<value>[^.\n]+)",
        ),
        "mode": (
            r"(?P<label>training\s+mode)\s*[:\-]\s*(?P<value>[^.\n]+)",
            r"(?P<label>mode)\s*[:\-]\s*(?P<value>[^.\n]+)",
        ),
        "certificate": (
            r"(?P<label>(?:completion\s+)?certificate(?:s)?)\s*[:\-]\s*(?P<value>[^.\n]+)",
            r"(?P<label>certificate)\s*(?:is|are)\s*[:\-]?\s*(?P<value>[^.\n]+)",
        ),
        "payment": (
            r"(?P<label>payment(?:\s+method|\s+options?)?)\s*[:\-]\s*(?P<value>[^.\n]+)",
            r"(?P<label>payment)\s*(?:is|can be|may be)\s*[:\-]?\s*(?P<value>[^.\n]+)",
        ),
        "eligibility": (
            r"(?P<label>eligibility|requirements?|qualifications?)\s*[:\-]\s*(?P<value>[^.\n]+)",
            r"(?P<label>who\s+can\s+join)\s*[:\-]?\s*(?P<value>[^.\n]+)",
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
        if intent in {"details", "company_information"} or response_style == "long":
            return self._summary(items, response_style)
        return None

    def _fact_answer(self, items: list[object], field: str) -> str | None:
        answers: list[str] = []
        seen: set[str] = set()
        labels = self.FACT_LABELS[field]
        for item in items:
            title = self._clean_title(getattr(item, "title", ""))
            content = self._clean_preserve_lines(getattr(item, "content", ""))
            if not content:
                continue
            extracted = self._source_fact_sentence(content, field)
            if extracted:
                key = self._fact_key(extracted)
                if key and key not in seen:
                    seen.add(key)
                    answers.append(self._with_title(title, extracted))
            else:
                for piece in self._pieces(content):
                    if not self._contains_fact(piece, labels):
                        continue
                    key = self._fact_key(piece)
                    if key and key not in seen:
                        seen.add(key)
                        answers.append(self._with_title(title, self._sentence(piece)))
                    break
            if len(answers) >= 4:
                break
        return " ".join(answers) if answers else None

    @classmethod
    def _source_fact_sentence(cls, content: str, field: str) -> str | None:
        pieces = cls._pieces(content)
        for index, piece in enumerate(pieces):
            if not cls._contains_fact(piece, cls.FACT_LABELS[field]):
                continue
            extracted = cls._extract_field(piece, field)
            if extracted:
                if field == "fee" and index + 1 < len(pieces):
                    next_piece = pieces[index + 1]
                    if cls._looks_like_supporting_payment_detail(next_piece):
                        return f"{cls._sentence(piece)} {cls._sentence(next_piece)}"
                return extracted
            if field in {"mode", "certificate", "payment", "eligibility", "discount", "contact"}:
                return cls._sentence(piece)
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
            if field in {"timings", "duration", "mode"}:
                return value.rstrip(".")
            if re.match(r"^(?:the\s+)?(?:fee|fees|price|pricing|cost|tuition)$", label, re.IGNORECASE):
                return cls._sentence(content)
            if re.match(r"^(?:completion\s+)?certificate(?:s)?$", label, re.IGNORECASE):
                return cls._sentence(content)
            return cls._sentence(content)
        return None

    @classmethod
    def _topics_answer(cls, items: list[object]) -> str | None:
        results: list[str] = []
        seen: set[str] = set()
        for item in items:
            title = cls._clean_title(getattr(item, "title", ""))
            content = cls._clean_preserve_lines(getattr(item, "content", ""))
            for piece in cls._pieces(content):
                match = re.search(r"(?:topics?|syllabus|curriculum|content)\s*[:\-]\s*(.+)", piece, re.IGNORECASE)
                if match:
                    candidate = match.group(1).strip(" .")
                elif cls._looks_like_topic_sentence(piece):
                    candidate = piece.strip()
                else:
                    continue
                key = cls._fact_key(candidate)
                if key and key not in seen:
                    seen.add(key)
                    results.append(cls._with_title(title, candidate))
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
            content = cls._clean_preserve_lines(getattr(item, "content", ""))
            candidates: list[str] = []
            for line in cls._pieces(content):
                match = re.search(r"(?:course|program|training|service|product)\s*(?:name|title)?\s*[:\-]\s*(.+)", line, re.IGNORECASE)
                if match:
                    candidates.append(match.group(1).strip(" ."))
            if title and not cls._generic_title(title):
                candidates.insert(0, title)
            for candidate in candidates:
                candidate = re.sub(r"\s+", " ", candidate).strip(" -:")
                key = candidate.lower()
                if key and key not in seen:
                    seen.add(key)
                    names.append(candidate)
        return "We currently offer: " + ", ".join(names) + "." if names else None

    @staticmethod
    def _generic_title(title: str) -> bool:
        return bool(re.search(r"^(?:company|knowledge|faq|general|uploaded|document)\b", title, re.IGNORECASE))

    @classmethod
    def _summary(cls, items: list[object], response_style: str) -> str | None:
        max_chars = 2200 if response_style == "long" else 1500
        blocks: list[str] = []
        used = 0
        for item in items[:6]:
            title = cls._clean_title(getattr(item, "title", ""))
            content = cls._clean_preserve_lines(getattr(item, "content", ""))
            if not content:
                continue
            block = cls._with_title(title, content)
            remaining = max_chars - used
            if remaining <= 0:
                break
            if len(block) > remaining:
                block = block[: max(0, remaining - 3)].rstrip() + "..."
            blocks.append(block)
            used += len(block) + 2
        return " ".join(blocks) if blocks else None

    @staticmethod
    def _join_answers(*answers: str | None) -> str | None:
        values = [value for value in answers if value]
        return " ".join(values) if values else None

    @classmethod
    def _contains_fact(cls, text: str, labels: set[str]) -> bool:
        normalized = (text or "").lower()
        return any(re.search(rf"(?<![a-z0-9+#]){re.escape(label)}(?![a-z0-9+#])", normalized) for label in labels)

    @staticmethod
    def _looks_like_supporting_payment_detail(piece: str) -> bool:
        lower = piece.lower()
        return any(term in lower for term in ("installment", "installments", "payment", "pay", "advance", "full payment"))

    @staticmethod
    def _sentence(value: str) -> str:
        text = re.sub(r"\s+", " ", value or "").strip()
        return text if not text or text.endswith((".", "!", "?")) else text + "."

    @staticmethod
    def _pieces(text: str) -> list[str]:
        return [part.strip(" •\t") for part in re.split(r"(?<=[.!?])\s+|\r?\n+|\s+(?=•\s+)|\s+(?=-\s+)", text) if part.strip()]

    @classmethod
    def _fact_key(cls, value: str) -> str:
        text = cls._clean(value).lower()
        text = re.sub(r"^[^:]+:\s*", "", text)
        text = re.sub(r"^the\s+", "", text)
        return re.sub(r"\s+", " ", text).strip(" .")

    @staticmethod
    def _with_title(title: str, value: str) -> str:
        return f"{title}: {value}" if title else value

    @staticmethod
    def _clean(value: object) -> str:
        return re.sub(r"\s+", " ", str(value or "")).strip()

    @classmethod
    def _clean_title(cls, value: object) -> str:
        return cls._clean(value).strip("-:#")[:160]

    @staticmethod
    def _clean_preserve_lines(value: object) -> str:
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in str(value or "").replace("\r", "").split("\n")]
        return "\n".join(line for line in lines if line)
