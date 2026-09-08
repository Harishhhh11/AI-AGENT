"""Deterministic response synthesis from verified organization knowledge."""

from __future__ import annotations

import re


class KnowledgeAnswerService:
    """Build customer-facing answers from retrieved, tenant-scoped knowledge."""

    FACT_LABELS = {
        "fee": {"fee", "fees", "price", "pricing", "cost", "costs", "tuition"},
        "duration": {"duration", "length", "months", "weeks", "days"},
        "timings": {"timing", "timings", "schedule", "batch", "morning", "evening"},
        "mode": {"online", "offline", "classroom", "mode", "remote", "remotely"},
        "contact": {"phone", "mobile", "email", "address", "location", "contact"},
    }

    def answer(self, *, items: list[object], intent: str, subject: str | None, response_style: str) -> str | None:
        if not items:
            return None
        if intent in self.FACT_LABELS:
            return self._fact_answer(items, self.FACT_LABELS[intent])
        if intent in {"details", "company_courses", "topics", "availability"} or response_style == "long":
            return self._summary(items, response_style)
        return None

    def _fact_answer(self, items: list[object], labels: set[str]) -> str | None:
        answers: list[str] = []
        seen: set[str] = set()
        for item in items:
            title = self._clean(getattr(item, "title", ""))
            content = self._clean(getattr(item, "content", ""))
            sentences = self._sentences(content)
            matching = [sentence for sentence in sentences if any(re.search(rf"\b{re.escape(label)}\b", sentence.lower()) for label in labels)]
            if matching:
                key = " ".join(matching[:2]).lower()
                if key in seen:
                    continue
                seen.add(key)
                answers.append(f"{title}: {' '.join(matching[:2])}" if title else " ".join(matching[:2]))
            if len(answers) >= 4:
                break
        return " ".join(answers) if answers else None

    def _summary(self, items: list[object], response_style: str) -> str | None:
        parts: list[str] = []
        max_chars = 1800 if response_style == "long" else 1200
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
            parts.append(block)
            used += len(block) + 1
            if len(parts) >= 4:
                break
        return " ".join(parts) if parts else None

    @staticmethod
    def _sentences(text: str) -> list[str]:
        return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]

    @staticmethod
    def _clean(value: object) -> str:
        return re.sub(r"\s+", " ", str(value or "")).strip()
