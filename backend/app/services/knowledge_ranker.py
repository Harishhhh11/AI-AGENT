"""Deterministic hybrid ranking for retrieved knowledge candidates."""

from __future__ import annotations

from app.services.relevance_service import RelevanceService


class KnowledgeRanker:
    """Rank already tenant-scoped candidates using lexical and semantic evidence."""

    def __init__(self) -> None:
        self.relevance = RelevanceService()

    def rank(self, *, query: str, items: list[object], limit: int = 5) -> list[object]:
        if not items:
            return []
        try:
            limit = max(1, int(limit))
        except (TypeError, ValueError):
            limit = 5

        # Company-wide prompts such as "what courses do you offer?" can contain
        # no meaningful subject terms after stop-word removal. In that case the
        # KnowledgeService has already produced the best tenant-scoped candidates;
        # preserve their order instead of incorrectly treating them as irrelevant.
        meaningful_terms = self.relevance._meaningful_terms(query)
        if not meaningful_terms:
            return list(items[:limit])

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
            scored.append((result.combined_score, result.lexical_score, -(getattr(item, "id", 0) or 0), item))

        scored.sort(key=lambda row: (row[0], row[1], row[2]), reverse=True)
        return [row[3] for row in scored[:limit]]
