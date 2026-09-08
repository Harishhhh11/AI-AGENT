"""Deterministic response synthesis from verified knowledge."""

from __future__ import annotations

import re


class KnowledgeAnswerService:
    """Build useful customer-facing answers from verified knowledge."""

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
            return self._fact_answer(items, {"fee", "fees", "price", "pricing", "cost", "costs", "tuition"})
        if intent == "duration":
            return self._fact_answer(items, {"duration", "length", "months", "weeks", "days"})
        if intent == "timings":
            return self._fact_answer(items, {"timing", "timings", "schedule", "batch", "morning", "evening"})
        if intent == "mode":
            return self._fact_answer(items, {"online", "offline", "classroom", "mode"})
        if intent == "contact":
            return self._fact_answer(items, {"phone", "mobile", "email", "address", "location", "contact"})
        if intent in {"details", "company_courses", "topics"} or response_style == "long":
            return self._summary(items)
        return None

    def _fact_answer(self, items: list[object], labels: set[str]) -> str | None:
        matches: list[str] = []
        for item in items:
            title = str(getattr(item, "title", "") or "").strip()
            content = str(getattr(item, "content", "") or "").strip()
            sentences = self._sentences(content)
            item_matches = [
                sentence
                for sentence in sentences
                if any(re.search(rf"\b{re.escape(label)}\b", sentence.lower()) for label in labels)
            ]
            if item_matches:
                prefix = f"{title}: " if title else ""
                matches.append(prefix + " ".join(item_matches[:2]))
            if len(matches) >= 3:
                break
        return " ".join(matches) if matches else None

    def _summary(self, items: list[object]) -> str | None:
        parts: list[str] = []
        for item in items:
            title = str(getattr(item, "title", "") or "").strip()
            content = str(getattr(item, "content", "") or "").strip()
            if not content:
                continue
            # Keep a larger, coherent excerpt so list-style knowledge such as
            # topics/courses is not reduced to only the first sentence.
            excerpt = re.sub(r"\s+", " ", content).strip()
            if len(excerpt) > 900:
                excerpt = excerpt[:897].rstrip() + "..."
            parts.append(f"{title}: {excerpt}" if title else excerpt)
            if len(parts) >= 3:
                break
        return " ".join(parts) if parts else None

    @staticmethod
    def _sentences(text: str) -> list[str]:
        cleaned = re.sub(r"\s+", " ", text or "").strip()
        return [part.strip() for part in re.split(r"(?<=[.!?])\s+", cleaned) if part.strip()]
