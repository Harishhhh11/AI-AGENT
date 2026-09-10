"""Deterministic response synthesis from verified organization knowledge."""

from __future__ import annotations

import re


class KnowledgeAnswerService:
    """Build concise customer-facing answers from retrieved, tenant-scoped facts."""

    FACT_LABELS = {
        "fee": {"fee", "fees", "price", "pricing", "cost", "costs", "tuition"},
        "discount": {"discount", "discounts", "concession", "reduction", "offer"},
        "duration": {"duration", "length", "months", "weeks", "days"},
        "timings": {"timing", "timings", "schedule", "batch", "morning", "evening", "start"},
        "mode": {"online", "offline", "classroom", "mode", "remote", "remotely"},
        "contact": {"phone", "mobile", "email", "address", "location", "contact"},
    }

    SUPPORTING_DETAIL_TERMS = {
        "available", "availability", "installment", "installments", "include", "includes", "included",
        "eligibility", "requirement", "requirements", "required", "benefit", "benefits", "certificate",
        "certification", "placement", "placements", "discount", "discounts", "offer", "offers",
        "registration", "admission", "admissions", "batch", "batches", "weekday", "weekend",
    }

    COURSE_HEADING_PATTERN = re.compile(
        r"(?:^|\n|[.;])\s*(?:course|program|training|service|product)\s*(?:name|title)?\s*[:\-]\s*([^\n.;]+)",
        re.IGNORECASE,
    )

    TOPIC_HEADING_TERMS = {"topic", "topics", "syllabus", "curriculum", "covered", "cover", "content"}

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
        if intent == "duration_and_timings":
            return self._join_answers(self._fact_answer(items, "duration"), self._fact_answer(items, "timings"))
        if intent in self.FACT_LABELS:
            return self._fact_answer(items, intent)
        if intent == "company_courses":
            return self._course_catalog(items)
        if intent == "topics":
            return self._topics_answer(items)
        if intent in {"details", "availability", "company_information"} or response_style == "long":
            return self._summary(items, response_style, company_wide=intent in {"availability", "company_information"})
        return None

    def _fact_answer(self, items: list[object], field: str) -> str | None:
        answers: list[str] = []
        seen_facts: set[str] = set()
        labels = self.FACT_LABELS[field]
        for item in items:
            title = self._clean(getattr(item, "title", ""))
            content = self._clean_preserve_lines(getattr(item, "content", ""))
            if not content:
                continue
            source_fact = self._source_fact_sentence(content, field)
            if source_fact:
                fact_key = self._fact_key(source_fact)
                if fact_key in seen_facts:
                    continue
                answer_text = f"{title}: {source_fact}" if title else source_fact
                answers.append(answer_text)
                seen_facts.add(fact_key)
            else:
                pieces = self._pieces(content)
                matching = [piece for piece in pieces if self._contains_fact(piece, labels)]
                for piece in self._attach_supporting_details(pieces, matching)[:6]:
                    fact_key = self._fact_key(piece)
                    if fact_key and fact_key not in seen_facts:
                        seen_facts.add(fact_key)
                        answers.append(f"{title}: {piece}" if title else piece)
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
            if not extracted:
                continue
            result = extracted if field in {"timings", "duration", "mode"} else piece.strip()
            if index + 1 < len(pieces):
                candidate = pieces[index + 1]
                candidate_terms = set(re.findall(r"[a-z0-9+#.-]+", candidate.lower()))
                if candidate_terms & cls.SUPPORTING_DETAIL_TERMS:
                    result = f"{result} {candidate.strip()}"
            return result.strip()
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
            if field in {"timings", "duration", "mode"}:
                return value.rstrip(".")
            return f"{label} {value}".strip()
        return None

    @classmethod
    def _fact_key(cls, value: str) -> str:
        text = cls._clean(value).lower()
        text = re.sub(r"^[^:]+:\s*", "", text)
        text = re.sub(r"^the\s+", "", text)
        text = re.sub(r"\s+", " ", text)
        return text.rstrip(".")

    @classmethod
    def _normalize_fact(cls, value: str) -> str:
        return cls._fact_key(value)

    @classmethod
    def _course_catalog(cls, items: list[object]) -> str | None:
        names: list[str] = []
        seen: set[str] = set()
        for item in items:
            content = cls._clean_preserve_lines(getattr(item, "content", ""))
            title = cls._clean(getattr(item, "title", ""))
            candidates = [match.group(1).strip() for match in cls.COURSE_HEADING_PATTERN.finditer(content)]
            if not candidates and title and not re.search(r"company|knowledge|faq|general", title, re.IGNORECASE):
                candidates = [title]
            for candidate in candidates:
                candidate = re.sub(r"\s+", " ", candidate).strip(" -:")
                normalized = candidate.lower()
                if normalized and normalized not in seen:
                    seen.add(normalized)
                    names.append(candidate)
        if names:
            return "We currently offer: " + ", ".join(names) + "."

        fallback: list[str] = []
        for item in items:
            title = cls._clean(getattr(item, "title", ""))
            if title and not re.search(r"company|knowledge|faq|general", title, re.IGNORECASE):
                normalized = title.lower()
                if normalized not in seen:
                    seen.add(normalized)
                    fallback.append(title)
        return "We currently offer: " + ", ".join(fallback) + "." if fallback else None

    @classmethod
    def _topics_answer(cls, items: list[object]) -> str | None:
        answers: list[str] = []
        seen: set[str] = set()
        for item in items:
            title = cls._clean(getattr(item, "title", ""))
            content = cls._clean_preserve_lines(getattr(item, "content", ""))
            if not content:
                continue
            pieces = cls._pieces(content)
            for index, piece in enumerate(pieces):
                if not cls._contains_fact(piece, cls.TOPIC_HEADING_TERMS):
                    continue
                candidate = piece
                match = re.search(r"(?:topics?|syllabus|curriculum|content)\s*[:\-]\s*(.+)", piece, re.IGNORECASE)
                if match:
                    candidate = match.group(1).strip()
                if candidate.lower().startswith(("what is covered", "topics covered")):
                    candidate = piece
                dedupe = cls._fact_key(candidate)
                if dedupe and dedupe not in seen:
                    seen.add(dedupe)
                    answers.append(f"{title}: {candidate}" if title else candidate)
                if index + 1 < len(pieces):
                    next_piece = pieces[index + 1]
                    if not cls._contains_fact(next_piece, cls.FACT_LABELS["fee"]) and cls._looks_like_topic_continuation(next_piece):
                        dedupe = cls._fact_key(next_piece)
                        if dedupe and dedupe not in seen:
                            seen.add(dedupe)
                            answers.append(f"{title}: {next_piece}" if title else next_piece)
            if not answers and title:
                # The entire record may be a topic syllabus without an explicit
                # "Topics:" label. Avoid returning unrelated fees/contact facts.
                topic_lines = [piece for piece in pieces if cls._looks_like_topic_continuation(piece)]
                if topic_lines:
                    for piece in topic_lines[:6]:
                        dedupe = cls._fact_key(piece)
                        if dedupe and dedupe not in seen:
                            seen.add(dedupe)
                            answers.append(f"{title}: {piece}")
            if len(answers) >= 8:
                break
        return " ".join(answers) if answers else None

    @classmethod
    def _looks_like_topic_continuation(cls, piece: str) -> bool:
        lower = cls._clean(piece).lower()
        return any(token in lower for token in (
            "variable", "function", "oop", "object", "class", "loop", "string", "list", "tuple", "dictionary",
            "api", "project", "database", "sql", "power bi", "excel", "python", "java", "javascript", "react",
            "django", "flask", "fastapi", "machine learning", "data analysis", "programming",
        ))

    @classmethod
    def _summary(cls, items: list[object], response_style: str, company_wide: bool = False) -> str | None:
        parts: list[str] = []
        max_chars = 2200 if response_style == "long" else 1500
        used = 0
        for item in items:
            title = cls._clean(getattr(item, "title", ""))
            content = cls._clean_preserve_lines(getattr(item, "content", ""))
            if not content:
                continue
            remaining = max_chars - used
            if remaining <= 0:
                break
            excerpt = content if len(content) <= remaining else content[: max(0, remaining - 3)].rstrip() + "..."
            block = f"{title}: {excerpt}" if title else excerpt
            parts.append(f"• {block}" if company_wide else block)
            used += len(block) + 2
            if len(parts) >= 6:
                break
        if not parts:
            return None
        return ("Here’s what I found in the verified knowledge base:\n" + "\n".join(parts)) if company_wide else " ".join(parts)

    @classmethod
    def _attach_supporting_details(cls, pieces: list[str], matching: list[str]) -> list[str]:
        if len(matching) >= 2 or len(pieces) <= 1:
            return matching
        selected_indexes = [index for index, piece in enumerate(pieces) if piece in matching]
        expanded = list(matching)
        for index in selected_indexes:
            for neighbor in (index - 1, index + 1):
                if neighbor < 0 or neighbor >= len(pieces):
                    continue
                candidate = pieces[neighbor]
                if candidate in expanded:
                    continue
                candidate_terms = set(re.findall(r"[a-z0-9+#.-]+", cls._clean(candidate).lower()))
                if candidate_terms & cls.SUPPORTING_DETAIL_TERMS:
                    expanded.append(candidate)
        expanded.sort(key=lambda piece: pieces.index(piece))
        return expanded

    @staticmethod
    def _contains_fact(text: str, labels: set[str]) -> bool:
        normalized = (text or "").lower()
        return any(re.search(rf"(?<![a-z0-9+#]){re.escape(label)}(?![a-z0-9+#])", normalized) for label in labels)

    @staticmethod
    def _join_answers(first: str | None, second: str | None) -> str | None:
        values = [value for value in (first, second) if value]
        return " ".join(values) if values else None

    @staticmethod
    def _pieces(text: str) -> list[str]:
        return [part.strip(" •\t") for part in re.split(r"(?<=[.!?])\s+|\r?\n+|\s+(?=•\s+)|\s+(?=-\s+)", text) if part.strip()]

    @staticmethod
    def _clean(value: object) -> str:
        return re.sub(r"\s+", " ", str(value or "")).strip()

    @staticmethod
    def _clean_preserve_lines(value: object) -> str:
        return re.sub(r"[ \t]+", " ", str(value or "")).strip()
