"""Deterministic response synthesis from verified organization knowledge."""

from __future__ import annotations

import re


class KnowledgeAnswerService:
    """Build customer-facing answers only from retrieved, tenant-scoped knowledge."""

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

    def answer(self, *, items: list[object], intent: str, subject: str | None, response_style: str) -> str | None:
        if not items:
            return None
        if intent == "duration_and_timings":
            return self._join_answers(
                self._fact_answer(items, self.FACT_LABELS["duration"]),
                self._fact_answer(items, self.FACT_LABELS["timings"]),
            )
        if intent in self.FACT_LABELS:
            return self._fact_answer(items, self.FACT_LABELS[intent])
        if intent in {"details", "company_courses", "topics", "availability", "company_information"} or response_style == "long":
            return self._summary(items, response_style, company_wide=intent in {"company_courses", "availability", "company_information"})
        return None

    def _fact_answer(self, items: list[object], labels: set[str]) -> str | None:
        answers: list[str] = []
        seen: set[str] = set()
        for item in items:
            title = self._clean(getattr(item, "title", ""))
            content = self._clean_preserve_lines(getattr(item, "content", ""))
            if not content:
                continue
            pieces = self._pieces(content)
            matching = [piece for piece in pieces if self._contains_fact(piece, labels)]
            if not matching and self._contains_fact(content, labels):
                matching = [content]
            if matching:
                matching = self._attach_supporting_details(pieces, matching)
            unique: list[str] = []
            for piece in matching[:6]:
                normalized = self._clean(piece).lower()
                if normalized and normalized not in seen:
                    seen.add(normalized)
                    unique.append(self._clean(piece))
            if unique:
                answers.append(f"{title}: {' '.join(unique)}" if title else " ".join(unique))
            if len(answers) >= 4:
                break
        return " ".join(answers) if answers else None

    @classmethod
    def _attach_supporting_details(cls, pieces: list[str], matching: list[str]) -> list[str]:
        """Keep adjacent facts that clarify a verified answer instead of truncating them."""
        if len(matching) >= 2 or len(pieces) <= 1:
            return matching
        selected_indexes = [pieces.index(piece) for piece in matching if piece in pieces]
        expanded = list(matching)
        for index in selected_indexes:
            for neighbor in (index - 1, index + 1):
                if neighbor < 0 or neighbor >= len(pieces):
                    continue
                candidate = pieces[neighbor]
                if candidate in expanded:
                    continue
                normalized = cls._clean(candidate).lower()
                if any(term in normalized.split() for term in cls.SUPPORTING_DETAIL_TERMS):
                    expanded.append(candidate)
        expanded.sort(key=lambda piece: pieces.index(piece))
        return expanded

    def _summary(self, items: list[object], response_style: str, company_wide: bool = False) -> str | None:
        parts: list[str] = []
        max_chars = 2200 if response_style == "long" else 1500
        used = 0
        for item in items:
            title = self._clean(getattr(item, "title", ""))
            content = self._clean_preserve_lines(getattr(item, "content", ""))
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
        if company_wide:
            return "Here’s what I found in the verified knowledge base:\n" + "\n".join(parts)
        return " ".join(parts)

    @staticmethod
    def _contains_fact(text: str, labels: set[str]) -> bool:
        normalized = (text or "").lower()
        return any(
            re.search(rf"(?<![a-z0-9+#]){re.escape(label)}(?![a-z0-9+#])", normalized)
            for label in labels
        )

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
