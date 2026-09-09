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
    """Combine lexical and semantic evidence without weakening tenant scope."""

    MIN_ACCEPT_SCORE = 0.25
    STRONG_LEXICAL_SCORE = 0.50
    SEMANTIC_ONLY_MAX_DISTANCE = 0.36
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

    IRREGULAR_STEMS = {
        "courses": "course",
        "classes": "class",
        "fees": "fee",
        "prices": "price",
        "costs": "cost",
        "topics": "topic",
        "services": "service",
        "products": "product",
        "offers": "offer",
        "timings": "timing",
        "batches": "batch",
        "admissions": "admission",
        "programs": "program",
        "technologies": "technology",
    }

    def score(self, *, query: str, title: str, content: str, semantic_distance: float | None = None) -> RelevanceResult:
        query_terms = self._meaningful_terms(query)
        title_terms = self._tokens(title)
        content_terms = self._tokens(content)
        all_terms = title_terms | content_terms
        matched = tuple(sorted(term for term in query_terms if self._term_matches(term, all_terms)))
        coverage = len(matched) / len(query_terms) if query_terms else 0.0
        title_coverage = sum(self._term_matches(term, title_terms) for term in query_terms) / len(query_terms) if query_terms else 0.0
        phrase_bonus = 0.10 if self._normalize(query).strip("?.!,;:") in self._normalize(f"{title} {content}") else 0.0
        lexical = min(1.0, 0.65 * coverage + 0.25 * title_coverage + phrase_bonus)
        semantic = self._semantic_score(semantic_distance)
        combined = max(lexical, 0.72 * lexical + 0.28 * semantic)
        semantic_distance_value = self._safe_distance(semantic_distance)
        lexical_accept = bool(matched) and (lexical >= self.STRONG_LEXICAL_SCORE or combined >= self.MIN_ACCEPT_SCORE)
        semantic_accept = not matched and semantic_distance_value is not None and semantic_distance_value <= self.SEMANTIC_ONLY_MAX_DISTANCE
        accepted = lexical_accept or semantic_accept
        return RelevanceResult(
            lexical_score=round(lexical, 4),
            semantic_score=round(semantic, 4),
            combined_score=round(combined, 4),
            accepted=accepted,
            query_terms=tuple(sorted(query_terms)),
            matched_terms=matched,
        )

    @classmethod
    def has_meaningful_terms(cls, value: str) -> bool:
        return bool(cls._meaningful_terms(value))

    @classmethod
    def _meaningful_terms(cls, value: str) -> set[str]:
        return {token for token in cls._tokens(value) if token not in cls.GENERIC_TERMS and len(token) > 1}

    @classmethod
    def _term_matches(cls, term: str, candidates: set[str]) -> bool:
        stem = cls.IRREGULAR_STEMS.get(term, term)
        for candidate in candidates:
            candidate_stem = cls.IRREGULAR_STEMS.get(candidate, candidate)
            if candidate == term or candidate_stem == stem:
                return True
            if len(stem) > 3 and (candidate.startswith(stem) or stem.startswith(candidate)):
                return True
        return False

    @staticmethod
    def _tokens(value: str) -> set[str]:
        return {token for token in re.findall(r"[a-z0-9+#.-]+", (value or "").lower()) if len(token) > 1}

    @staticmethod
    def _normalize(value: str) -> str:
        return " ".join((value or "").lower().split())

    @staticmethod
    def _safe_distance(distance: float | None) -> float | None:
        if distance is None:
            return None
        try:
            value = float(distance)
        except (TypeError, ValueError):
            return None
        return value if 0.0 <= value <= 1.0 else None

    @classmethod
    def _semantic_score(cls, distance: float | None) -> float:
        value = cls._safe_distance(distance)
        if value is None:
            return 0.0
        return max(0.0, min(1.0, 1.0 - value))
