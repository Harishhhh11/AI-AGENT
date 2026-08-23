"""Focused contracts for Phase 3 tool-execution orchestration."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.tools.base import ToolContext, ToolResult
from app.tools.registry import ToolOrchestrator, ToolRegistry


class FakeTool:
    name = "safe_tool"
    description = "A safe test tool."
    input_schema = {"type": "object"}
    requires_confirmation = False

    async def execute(self, context: ToolContext, arguments=None) -> ToolResult:
        return ToolResult(self.name, True, "ok", data={"arguments": arguments or {}})


class ConfirmationTool(FakeTool):
    name = "confirmation_tool"
    requires_confirmation = True


def build_context() -> ToolContext:
    return MagicMock(spec=ToolContext)


@pytest.mark.asyncio
async def test_execute_runs_registered_tool() -> None:
    registry = ToolRegistry(tools=[FakeTool()])
    orchestrator = ToolOrchestrator(registry=registry)

    result = await orchestrator.execute(
        "safe_tool",
        build_context(),
        {"value": 1},
    )

    assert result.success is True
    assert result.data == {"arguments": {"value": 1}}


@pytest.mark.asyncio
async def test_unknown_tool_returns_structured_failure() -> None:
    orchestrator = ToolOrchestrator(registry=ToolRegistry(tools=[FakeTool()]))

    result = await orchestrator.execute("missing_tool", build_context(), {})

    assert result.success is False
    assert result.error == "tool_not_found"


@pytest.mark.asyncio
async def test_confirmation_required_tool_is_not_executed() -> None:
    tool = ConfirmationTool()
    tool.execute = AsyncMock(side_effect=AssertionError("must not execute"))
    registry = ToolRegistry(tools=[tool])
    orchestrator = ToolOrchestrator(registry=registry)

    llm = MagicMock()
    orchestrator.planner.decide = AsyncMock(
        return_value=[MagicMock(name="confirmation_tool", arguments={})]
    )

    results = await orchestrator.decide_and_execute(llm, build_context())

    assert len(results) == 1
    assert results[0].success is False
    assert results[0].error == "confirmation_required"
    tool.execute.assert_not_awaited()
