"""Company-agnostic response length planning."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ResponsePlan:
    style: str
    max_characters: int
    question_count: int
    requires_knowledge: bool


class ResponsePolicyService:
    """Choose a bounded answer style from conversational signals."""

    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"

    SHORT_LIMIT = 350
    MEDIUM_LIMIT = 900
    LONG_LIMIT = 1800

    def plan(self, *, message: str, intent: str, question_count: int = 1, requires_knowledge: bool = False) -> ResponsePlan:
        text = (message or "").strip().lower()
        count = max(1, int(question_count or 1))
        if intent in {"details", "general_details"} or any(marker in text for marker in ("complete details", "everything", "all details", "in detail")):
            style = self.LONG
        elif count > 1 or intent in {"duration_and_timings", "comparison", "multi_part"} or any(marker in text for marker in (" and ", " also ", " plus ")):
            style = self.MEDIUM
        else:
            style = self.SHORT
        limit = {self.SHORT: self.SHORT_LIMIT, self.MEDIUM: self.MEDIUM_LIMIT, self.LONG: self.LONG_LIMIT}[style]
        return ResponsePlan(style=style, max_characters=limit, question_count=count, requires_knowledge=requires_knowledge)
