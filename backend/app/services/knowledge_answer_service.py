"""Deterministic response synthesis from verified knowledge."""

from __future__ import annotations

import re


class KnowledgeAnswerService:
    """Build concise customer-facing answers from retrieved knowledge."""

    def answer(
        self,
        *,
        items: list[object],
        intent: str,
        subject: str | None,
        response_style: str,
    ) -> str | None:
        if not items:
            return None

        if intent == "fee":
            return self._fact_sentence(items, {"fee", "fees", "price", "pricing", "cost", "costs", "tuition"})
        if intent == "duration":
            return self._fact_sentence(items, {"duration", "length", "months", "weeks", "days"})
        if intent == "timings":
            return self._fact_sentence(items, {"timing", "timings", "schedule", "batch", "morning", "evening"})
        if intent == "mode":
            return self._fact_sentence(items, {"online", "offline", "classroom", "mode"})
        if intent == "contact":
            return self._fact_sentence(items, {"phone", "mobile", "email", "address", "location", "contact"})
        if intent in {"details", "company_courses"} or response_style == "long":
            return self._summary(items)
        return None

    def _fact_sentence(self, items: list[object], labels: set[str]) -> str | None:
        for item in items:
            sentences = self._sentences(str(getattr(item, "content", "") or ""))
            matches = [sentence for sentence in sentences if any(label in sentence.lower() for label in labels)]
            if matches:
                return " ".join(matches[:2])
        return None

    def _summary(self, items: list[object]) -> str | None:
        parts: list[str] = []
        for item in items:
            title = str(getattr(item, "title", "") or "").strip()
            sentences = self._sentences(str(getattr(item, "content", "") or ""))
            if not sentences:
                continue
            parts.append(f"{title}: {sentences[0]}" if title else sentences[0])
            if len(parts) >= 3:
                break
        return " ".join(parts) if parts else None

    @staticmethod
    def _sentences(text: str) -> list[str]:
        cleaned = re.sub(r"\s+", " ", text or "").strip()
        return [part.strip() for part in re.split(r"(?<=[.!?])\s+", cleaned) if part.strip()]
