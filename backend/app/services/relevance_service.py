"""Company-agnostic relevance and grounding scoring."""

from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class RelevanceResult:
    lexical_score: float
    semantic_score: float
    combined_score: float
    accepted: bool
    query_terms: tuple[str, ...] = ()
    matched_terms: tuple[str, ...] = ()


class RelevanceService:
    """Combine lexical and semantic evidence while avoiding subject leakage."""

    MIN_ACCEPT_SCORE = 0.25
    STRONG_LEXICAL_SCORE = 0.50
    GENERIC_TERMS = {
        "what", "which", "how", "when", "where", "why", "who", "does", "do", "did", "is", "are", "am",
        "can", "could", "would", "will", "should", "you", "your", "we", "our", "i", "me", "my", "the",
        "a", "an", "for", "to", "of", "in", "on", "at", "about", "tell", "give", "provide", "please",
        "much", "many", "more", "details", "detail", "information", "info", "course", "courses", "class",
        "classes", "training", "service", "services", "product", "products", "available", "offer", "offers",
        "price", "pricing", "cost", "costs", "fee", "fees", "duration", "timing", "timings", "schedule",
        "topics", "topic", "covered", "cover", "syllabus", "mode", "online", "offline", "classroom", "contact",
        "phone", "email", "address", "location", "admission", "registration", "batch", "started", "start",
        "everything", "complete", "full", "company", "business", "organization",
    }

    def score(self, *, query: str, title: str, content: str, semantic_distance: float | None = None) -> RelevanceResult:
        query_terms = self._meaningful_terms(query)
        title_terms = self._tokens(title)
        content_terms = self._tokens(content)
        all_terms = title_terms | content_terms
        matched = tuple(sorted(query_terms & all_terms))
        coverage = len(matched) / len(query_terms) if query_terms else 0.0
        title_coverage = len(query_terms & title_terms) / len(query_terms) if query_terms else 0.0
        phrase_bonus = 0.10 if self._normalize(query).strip("?.!,;:") in self._normalize(f"{title} {content}") else 0.0
        lexical = min(1.0, 0.65 * coverage + 0.25 * title_coverage + phrase_bonus)
        semantic = self._semantic_score(semantic_distance)
        combined = max(lexical, 0.72 * lexical + 0.28 * semantic)
        # Semantic similarity can help paraphrases only after a subject signal
        # exists; unrelated records must never become grounded by similarity alone.
        accepted = bool(matched) and (lexical >= self.STRONG_LEXICAL_SCORE or combined >= self.MIN_ACCEPT_SCORE)
        return RelevanceResult(
            lexical_score=round(lexical, 4),
            semantic_score=round(semantic, 4),
            combined_score=round(combined, 4),
            accepted=accepted,
            query_terms=tuple(sorted(query_terms)),
            matched_terms=matched,
        )

    @classmethod
    def _meaningful_terms(cls, value: str) -> set[str]:
        return {token for token in cls._tokens(value) if token not in cls.GENERIC_TERMS and len(token) > 1}

    @staticmethod
    def _tokens(value: str) -> set[str]:
        return {token for token in re.findall(r"[a-z0-9+#.-]+", (value or "").lower()) if len(token) > 1}

    @staticmethod
    def _normalize(value: str) -> str:
        return " ".join((value or "").lower().split())

    @staticmethod
    def _semantic_score(distance: float | None) -> float:
        if distance is None:
            return 0.0
        try:
            return max(0.0, min(1.0, 1.0 - float(distance)))
        except (TypeError, ValueError):
            return 0.0
