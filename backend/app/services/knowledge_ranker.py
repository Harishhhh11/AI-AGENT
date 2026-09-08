"""Deterministic ranking for retrieved company knowledge."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class RankedKnowledge:
    item: object
    score: float


class KnowledgeRanker:
    """Rank retrieved knowledge using lexical and semantic evidence."""

    def rank(self, *, query: str, items: list[object], limit: int) -> list[object]:
        if not items or not query:
            return list(items or [])[: max(0, limit)]

        ranked = [self._score(query, item) for item in items]
        ranked.sort(
            key=lambda result: (
                -result.score,
                -(getattr(result.item, "id", 0) or 0),
                str(getattr(result.item, "title", "") or "").lower(),
            )
        )
        return [result.item for result in ranked[: max(0, limit)]]

    def _score(self, query: str, item: object) -> RankedKnowledge:
        q = self._tokens(query)
        title = str(getattr(item, "title", "") or "")
        category = str(getattr(item, "category", "") or "")
        content = str(getattr(item, "content", "") or "")
        title_tokens = self._tokens(title)
        category_tokens = self._tokens(category)
        content_tokens = self._tokens(content)

        if not q:
            lexical = 0.0
        else:
            coverage = len(q & (title_tokens | category_tokens | content_tokens)) / len(q)
            title_coverage = len(q & title_tokens) / len(q)
            category_coverage = len(q & category_tokens) / len(q)
            phrase_bonus = 0.10 if self._normalized(query) in self._normalized(title + " " + content) else 0.0
            lexical = min(1.0, 0.60 * coverage + 0.25 * title_coverage + 0.05 * category_coverage + phrase_bonus)

        semantic_distance = getattr(item, "semantic_distance", None)
        try:
            semantic = max(0.0, min(1.0, 1.0 - float(semantic_distance))) if semantic_distance is not None else 0.0
        except (TypeError, ValueError):
            semantic = 0.0

        return RankedKnowledge(item=item, score=round(max(lexical, 0.75 * lexical + 0.25 * semantic), 4))

    @staticmethod
    def _tokens(value: str) -> set[str]:
        return {token for token in re.findall(r"[a-z0-9+#.-]+", (value or "").lower()) if len(token) > 1}

    @staticmethod
    def _normalized(value: str) -> str:
        return " ".join((value or "").lower().split()).strip("?.!,;:")
