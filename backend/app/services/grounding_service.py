"""Company-agnostic grounding gate for retrieved knowledge."""

from dataclasses import dataclass

from app.services.relevance_service import RelevanceResult, RelevanceService


@dataclass(frozen=True)
class GroundingDecision:
    accepted: bool
    score: float
    reason: str
    relevance: RelevanceResult


class GroundingService:
    """Allow retrieved knowledge through only when relevance is sufficient."""

    def __init__(self, relevance_service: RelevanceService | None = None) -> None:
        self.relevance_service = relevance_service or RelevanceService()

    def evaluate(
        self,
        *,
        query: str,
        title: str,
        content: str,
        semantic_distance: float | None = None,
    ) -> GroundingDecision:
        relevance = self.relevance_service.score(
            query=query,
            title=title,
            content=content,
            semantic_distance=semantic_distance,
        )

        # Broad company questions (for example, "Which courses do you offer?")
        # intentionally have no subject-specific terms after normalization. The
        # candidates have already been restricted by organization/agent scope and
        # retrieved from the verified knowledge base, so they remain valid sources.
        if not self.relevance_service.has_meaningful_terms(query):
            return GroundingDecision(
                accepted=True,
                score=0.0,
                reason="accepted broad verified knowledge query",
                relevance=relevance,
            )

        accepted = relevance.accepted
        reason = "accepted" if accepted else "insufficient relevance"
        return GroundingDecision(
            accepted=accepted,
            score=relevance.combined_score,
            reason=reason,
            relevance=relevance,
        )
