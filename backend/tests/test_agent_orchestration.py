"""Phase 3 orchestration planning contracts."""

from app.services.agent_orchestration_service import (
    AgentOrchestrationService,
    ExecutionMode,
)


def test_direct_requests_do_not_invoke_tools() -> None:
    plan = AgentOrchestrationService().plan(
        message="Tell me a quick joke",
        intent="general",
        requires_knowledge=False,
    )

    assert plan.mode is ExecutionMode.DIRECT
    assert plan.tool_name is None
    assert plan.steps == ()


def test_tool_intent_selects_deterministic_tool() -> None:
    plan = AgentOrchestrationService().plan(
        message="I want to contact the company",
        intent="contact",
        requires_knowledge=False,
    )

    assert plan.mode is ExecutionMode.TOOL
    assert plan.tool_name == "contact_lookup"
    assert plan.steps == ("contact_lookup",)


def test_knowledge_requirement_routes_to_knowledge_lookup() -> None:
    plan = AgentOrchestrationService().plan(
        message="What is the course fee?",
        intent="fee",
        requires_knowledge=True,
    )

    assert plan.mode is ExecutionMode.TOOL
    assert plan.tool_name == "knowledge_lookup"


def test_multi_step_intent_returns_ordered_steps() -> None:
    plan = AgentOrchestrationService().plan(
        message="Capture my details and arrange follow-up",
        intent="lead_capture_and_follow_up",
        requires_knowledge=False,
    )

    assert plan.mode is ExecutionMode.MULTI_STEP
    assert plan.steps == ("lead_capture", "follow_up")
    assert plan.tool_name is None
