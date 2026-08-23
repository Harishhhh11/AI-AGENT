from __future__ import annotations

import pytest

from app.tools.base import BaseTool, ToolContext, ToolResult
from app.tools.registry import ToolOrchestrator, ToolRegistry


class FlakyTool(BaseTool):
    name = "flaky_tool"
    description = "Fails once, then succeeds."
    requires_confirmation = False

    def __init__(self) -> None:
        self.calls = 0

    @property
    def input_schema(self) -> dict:
        return {"type": "object"}

    async def execute(self, context: ToolContext, arguments: dict | None = None) -> ToolResult:
        self.calls += 1
        if self.calls == 1:
            return ToolResult(self.name, False, "temporary failure", error="temporary_error")
        return ToolResult(self.name, True, "recovered")


class SuccessTool(BaseTool):
    requires_confirmation = False

    def __init__(self, name: str) -> None:
        self.name = name
        self.description = name

    @property
    def input_schema(self) -> dict:
        return {"type": "object"}

    async def execute(self, context: ToolContext, arguments: dict | None = None) -> ToolResult:
        return ToolResult(self.name, True, f"ran {self.name}")


@pytest.mark.asyncio
async def test_retryable_tool_can_recover() -> None:
    tool = FlakyTool()
    registry = ToolRegistry([tool])
    orchestrator = ToolOrchestrator(registry=registry)

    first = await orchestrator.execute(tool.name, ToolContext(db=None, organization_id=1))
    second = await orchestrator.execute(tool.name, ToolContext(db=None, organization_id=1))

    assert first.success is False
    assert second.success is True
    assert tool.calls == 2


@pytest.mark.asyncio
async def test_multistep_execution_preserves_order() -> None:
    first = SuccessTool("first_step")
    second = SuccessTool("second_step")
    registry = ToolRegistry([first, second])
    orchestrator = ToolOrchestrator(registry=registry)

    results = []
    for name in ["first_step", "second_step"]:
        results.append(await orchestrator.execute(name, ToolContext(db=None, organization_id=1)))

    assert [item.tool_name for item in results] == ["first_step", "second_step"]
    assert all(item.success for item in results)
