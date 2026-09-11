"""Deterministic hybrid ranking for retrieved knowledge candidates."""

from __future__ import annotations

import re

from app.services.relevance_service import RelevanceService


class KnowledgeRanker:
    DUPLICATE_CONTENT_THRESHOLD = 0.82

    def __init__(self) -> None:
        self.relevance = RelevanceService()

    def rank(self, *, query: str, items: list[object], limit: int = 5) -> list[object]:
        if not items:
            return []
        try:
            limit = max(1, int(limit))
        except (TypeError, ValueError):
            limit = 5

        meaningful_terms = self.relevance._meaningful_terms(query)
        if not meaningful_terms:
            return self._select_diverse(list(items), limit)

        scored: list[tuple[float, float, int, object]] = []
        for item in items:
            result = self.relevance.score(
                query=query,
                title=str(getattr(item, "title", "") or ""),
                content=str(getattr(item, "content", "") or ""),
                semantic_distance=getattr(item, "semantic_distance", None),
            )
            if not result.accepted:
                continue
            if not result.matched_terms:
                title_terms = self.relevance._meaningful_terms(str(getattr(item, "title", "") or ""))
                if title_terms and len(title_terms) <= 3:
                    continue
            scored.append((result.combined_score, result.lexical_score, -(getattr(item, "id", 0) or 0), item))

        scored.sort(key=lambda row: (row[0], row[1], row[2]), reverse=True)
        return self._select_diverse([row[3] for row in scored], limit)

    @classmethod
    def _select_diverse(cls, ordered_items: list[object], limit: int) -> list[object]:
        selected: list[object] = []
        skipped: list[object] = []
        for item in ordered_items:
            if len(selected) >= limit:
                break
            if cls._is_near_duplicate(item, selected):
                skipped.append(item)
                continue
            selected.append(item)
        for item in skipped:
            if len(selected) >= limit:
                break
            selected.append(item)
        return selected

    @classmethod
    def _is_near_duplicate(cls, item: object, selected: list[object]) -> bool:
        tokens = cls._content_tokens(item)
        if not tokens:
            return False
        for other in selected:
            other_tokens = cls._content_tokens(other)
            union = len(tokens | other_tokens)
            if union and len(tokens & other_tokens) / union >= cls.DUPLICATE_CONTENT_THRESHOLD:
                return True
        return False

    @staticmethod
    def _content_tokens(item: object) -> set[str]:
        return set(re.findall(r"[a-z0-9]+", str(getattr(item, "content", "") or "").lower()))
