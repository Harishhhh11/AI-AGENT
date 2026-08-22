"""Company-agnostic relevance scoring for retrieved knowledge."""

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class RelevanceResult:
    lexical_score: float
    semantic_score: float
    combined_score: float
    accepted: bool


class RelevanceService:
    """Combine lexical and optional semantic evidence before grounding."""

    MIN_ACCEPT_SCORE = 0.30
    STRONG_LEXICAL_SCORE = 0.60

    def score(
        self,
        *,
        query: str,
        title: str,
        content: str,
        semantic_distance: float | None = None,
    ) -> RelevanceResult:
        lexical = self._lexical_score(query, title, content)
        semantic = self._semantic_score(semantic_distance)
        combined = round(max(lexical, (0.65 * lexical) + (0.35 * semantic)), 4)
        accepted = lexical >= self.STRONG_LEXICAL_SCORE or combined >= self.MIN_ACCEPT_SCORE
        return RelevanceResult(lexical, semantic, combined, accepted)

    @staticmethod
    def _tokens(value: str) -> set[str]:
        return {
            token
            for token in re.findall(r"[a-z0-9]+", (value or "").lower())
            if len(token) > 1
        }

    def _lexical_score(self, query: str, title: str, content: str) -> float:
        q = self._tokens(query)
        if not q:
            return 0.0
        title_tokens = self._tokens(title)
        content_tokens = self._tokens(content)
        title_overlap = len(q & title_tokens) / len(q)
        content_overlap = len(q & content_tokens) / len(q)
        return min(1.0, (0.70 * title_overlap) + (0.30 * content_overlap))

    @staticmethod
    def _semantic_score(distance: float | None) -> float:
        if distance is None:
            return 0.0
        return max(0.0, min(1.0, 1.0 - float(distance)))
