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

    def evaluate(self, *, query: str, title: str, content: str, semantic_distance: float | None = None) -> GroundingDecision:
        relevance = self.relevance_service.score(
            query=query,
            title=title,
            content=content,
            semantic_distance=semantic_distance,
        )
        return GroundingDecision(
            accepted=relevance.accepted,
            score=relevance.combined_score,
            reason="accepted" if relevance.accepted else "insufficient relevance",
            relevance=relevance,
        )
