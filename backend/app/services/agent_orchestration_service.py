"""Company-agnostic orchestration planning for Phase 3."""

from dataclasses import dataclass
from enum import Enum


class ExecutionMode(str, Enum):
    DIRECT = "direct"
    TOOL = "tool"
    MULTI_STEP = "multi_step"


@dataclass(frozen=True)
class OrchestrationPlan:
    mode: ExecutionMode
    tool_name: str | None
    steps: tuple[str, ...]
    requires_confirmation: bool
    rationale: str


class AgentOrchestrationService:
    """Plan whether a request should be answered directly or executed via tools."""

    TOOL_INTENTS = {
        "lead_capture": "lead_capture",
        "contact": "contact_lookup",
        "company_information": "knowledge_lookup",
        "admission": "admission_lookup",
    }

    MULTI_STEP_INTENTS = {
        "lead_capture_and_follow_up": ("lead_capture", "follow_up"),
        "schedule_and_notify": ("schedule", "notify"),
    }

    def plan(self, *, message: str, intent: str, requires_knowledge: bool = False) -> OrchestrationPlan:
        normalized_intent = (intent or "").strip().lower()

        if normalized_intent in self.MULTI_STEP_INTENTS:
            return OrchestrationPlan(
                mode=ExecutionMode.MULTI_STEP,
                tool_name=None,
                steps=tuple(self.MULTI_STEP_INTENTS[normalized_intent]),
                requires_confirmation=False,
                rationale="Intent maps to a multi-step workflow.",
            )

        if normalized_intent in self.TOOL_INTENTS:
            return OrchestrationPlan(
                mode=ExecutionMode.TOOL,
                tool_name=self.TOOL_INTENTS[normalized_intent],
                steps=(self.TOOL_INTENTS[normalized_intent],),
                requires_confirmation=False,
                rationale="Intent requires a deterministic tool path.",
            )

        if requires_knowledge:
            return OrchestrationPlan(
                mode=ExecutionMode.TOOL,
                tool_name="knowledge_lookup",
                steps=("knowledge_lookup",),
                requires_confirmation=False,
                rationale="Knowledge is required for a grounded answer.",
            )

        return OrchestrationPlan(
            mode=ExecutionMode.DIRECT,
            tool_name=None,
            steps=(),
            requires_confirmation=False,
            rationale="No tool execution is required.",
        )
