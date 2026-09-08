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

    def answer(self, *, items: list[object], intent: str, subject: str | None, response_style: str) -> str | None:
        if not items:
            return None
        if intent == "duration_and_timings":
            duration = self._fact_answer(items, self.FACT_LABELS["duration"])
            timings = self._fact_answer(items, self.FACT_LABELS["timings"])
            return self._join_answers(duration, timings)
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
            content = self._clean(getattr(item, "content", ""))
            if not content:
                continue
            sentences = self._sentences(content)
            matching = [sentence for sentence in sentences if self._contains_fact(sentence, labels)]
            if not matching:
                # Knowledge uploads are not required to use sentence punctuation.
                # If the whole item is short and directly contains the requested
                # fact vocabulary, keep it grounded rather than returning a false miss.
                if self._contains_fact(content, labels):
                    matching = [content]
            if matching:
                unique = []
                for sentence in matching[:3]:
                    normalized = sentence.lower()
                    if normalized not in seen:
                        seen.add(normalized)
                        unique.append(sentence)
                if unique:
                    answers.append(f"{title}: {' '.join(unique)}" if title else " ".join(unique))
            if len(answers) >= 4:
                break
        return " ".join(answers) if answers else None

    def _summary(self, items: list[object], response_style: str, company_wide: bool = False) -> str | None:
        parts: list[str] = []
        max_chars = 2200 if response_style == "long" else 1500
        used = 0
        for item in items:
            title = self._clean(getattr(item, "title", ""))
            content = self._clean(getattr(item, "content", ""))
            if not content:
                continue
            remaining = max_chars - used
            if remaining <= 0:
                break
            excerpt = content if len(content) <= remaining else content[: max(0, remaining - 3)].rstrip() + "..."
            block = f"{title}: {excerpt}" if title else excerpt
            if company_wide:
                parts.append(f"• {block}")
            else:
                parts.append(block)
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
        return any(re.search(rf"(?<![a-z0-9+#]){re.escape(label)}(?![a-z0-9+#])", normalized) for label in labels)

    @staticmethod
    def _join_answers(first: str | None, second: str | None) -> str | None:
        values = [value for value in (first, second) if value]
        return " ".join(values) if values else None

    @staticmethod
    def _sentences(text: str) -> list[str]:
        return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]

    @staticmethod
    def _clean(value: object) -> str:
        return re.sub(r"\s+", " ", str(value or "")).strip()
