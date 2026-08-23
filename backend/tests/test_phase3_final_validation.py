from __future__ import annotations

import pytest

from app.tools.base import BaseTool, ToolContext, ToolResult
from app.tools.registry import ToolOrchestrator, ToolRegistry


class RecordingTool(BaseTool):
    requires_confirmation = False

    def __init__(self, name: str, calls: list[str], succeed: bool = True) -> None:
        self.name = name
        self.description = name
        self.calls = calls
        self.succeed = succeed

    @property
    def input_schema(self) -> dict:
        return {"type": "object"}

    async def execute(self, context: ToolContext, arguments: dict | None = None) -> ToolResult:
        self.calls.append(self.name)
        return ToolResult(self.name, self.succeed, f"ran {self.name}", error=None if self.succeed else "tool_failed")


@pytest.mark.asyncio
async def test_final_orchestration_executes_registered_tool() -> None:
    calls: list[str] = []
    tool = RecordingTool("final_tool", calls)
    orchestrator = ToolOrchestrator(registry=ToolRegistry([tool]))

    result = await orchestrator.execute(
        "final_tool",
        ToolContext(db=None, organization_id=1, message="run final tool"),
    )

    assert result.success is True
    assert calls == ["final_tool"]


@pytest.mark.asyncio
async def test_final_orchestration_preserves_bounded_step_order() -> None:
    calls: list[str] = []
    first = RecordingTool("step_one", calls)
    second = RecordingTool("step_two", calls)
    third = RecordingTool("step_three", calls)
    orchestrator = ToolOrchestrator(registry=ToolRegistry([first, second, third]))

    results = []
    for name in ("step_one", "step_two", "step_three"):
        results.append(
            await orchestrator.execute(
                name,
                ToolContext(db=None, organization_id=1, message=f"run {name}"),
            )
        )

    assert all(item.success for item in results)
    assert calls == ["step_one", "step_two", "step_three"]


@pytest.mark.asyncio
async def test_final_orchestration_keeps_failure_structured() -> None:
    tool = RecordingTool("failing_tool", [], succeed=False)
    orchestrator = ToolOrchestrator(registry=ToolRegistry([tool]))

    result = await orchestrator.execute(
        "failing_tool",
        ToolContext(db=None, organization_id=1),
    )

    assert result.success is False
    assert result.error == "tool_failed"
    assert result.tool_name == "failing_tool"
