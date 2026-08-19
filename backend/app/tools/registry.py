"""Tool registry and execution boundary."""

from __future__ import annotations

from typing import Any

from app.llm.base_llm import BaseLLM
from app.tools.base import BaseTool, ToolContext, ToolResult
from app.tools.integration_tools import default_integration_tools
from app.tools.lead_tools import SaveLeadTool
from app.tools.planner import ToolPlanner


class ToolRegistry:
    def __init__(self, tools: list[BaseTool] | None = None) -> None:
        self._tools: dict[str, BaseTool] = {}
        for tool in tools or [SaveLeadTool(), *default_integration_tools()]:
            self.register(tool)

    def register(self, tool: BaseTool) -> None:
        if not tool.name or tool.name in self._tools:
            raise ValueError(f"Invalid or duplicate tool name: {tool.name!r}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def descriptions(self) -> list[dict[str, Any]]:
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
                "requires_confirmation": tool.requires_confirmation,
            }
            for tool in self._tools.values()
        ]

    async def execute(
        self,
        name: str,
        context: ToolContext,
        arguments: dict[str, Any] | None = None,
    ) -> ToolResult:
        tool = self.get(name)
        if tool is None:
            return ToolResult(name, False, "Unknown tool.", error="tool_not_found")
        try:
            return await tool.execute(context, arguments)
        except Exception as exc:
            return ToolResult(name, False, "Tool execution failed.", error=str(exc))


class ToolOrchestrator:
    def __init__(self, registry: ToolRegistry | None = None, planner: ToolPlanner | None = None) -> None:
        self.registry = registry or ToolRegistry()
        self.planner = planner or ToolPlanner()

    async def execute(self, name: str, context: ToolContext, arguments: dict[str, Any] | None = None) -> ToolResult:
        return await self.registry.execute(name, context, arguments)

    async def decide_and_execute(self, llm: BaseLLM, context: ToolContext) -> list[ToolResult]:
        calls = await self.planner.decide(llm, context, self.registry.descriptions())
        results: list[ToolResult] = []
        for call in calls:
            # Provider tools remain confirmation/configuration gated. This
            # prevents a model from sending an external message accidentally.
            tool = self.registry.get(call.name)
            if tool is None or tool.requires_confirmation:
                results.append(ToolResult(call.name, False, "Tool requires configuration or confirmation." , error="confirmation_required"))
                continue
            results.append(await self.execute(call.name, context, call.arguments))
        return results
