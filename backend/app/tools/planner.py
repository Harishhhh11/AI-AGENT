"""Constrained LLM tool decision making."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from app.llm.base_llm import BaseLLM
from app.tools.base import ToolContext


@dataclass(slots=True)
class PlannedToolCall:
    name: str
    arguments: dict[str, Any] = field(default_factory=dict)
    reason: str = ""


class ToolPlanner:
    """Ask the model for a tool choice only for action-shaped messages."""

    ACTION_WORDS = re.compile(
        r"\b(send|email|mail|whatsapp|message|text|sheet|spreadsheet|"
        r"book|schedule|appointment|calendar|save|export|notify|call)\b",
        re.IGNORECASE,
    )

    def _may_need_tool(self, message: str) -> bool:
        return bool(self.ACTION_WORDS.search(message or ""))

    async def decide(
        self,
        llm: BaseLLM,
        context: ToolContext,
        tool_descriptions: list[dict[str, Any]],
    ) -> list[PlannedToolCall]:
        if not self._may_need_tool(context.message):
            return []

        prompt = f"""
You are the action planner for a customer-support receptionist.
Choose a tool only when the customer explicitly requests an action.
Never invent a tool. Never choose save_lead; lead persistence is automatic.
If no configured action is appropriate, return an empty list.

Available tools:
{json.dumps(tool_descriptions, ensure_ascii=True)}

Customer message:
{context.message}

Return only JSON in this shape:
{{"tool_calls":[{{"name":"send_email","arguments":{{}},"reason":"..."}}]}}
""".strip()

        try:
            raw = await llm.generate_structured(prompt)
            parsed = json.loads(raw)
        except Exception:
            return []

        calls = parsed.get("tool_calls", []) if isinstance(parsed, dict) else []
        if not isinstance(calls, list):
            return []

        allowed = {item["name"] for item in tool_descriptions}
        result: list[PlannedToolCall] = []
        for item in calls[:3]:
            if not isinstance(item, dict) or item.get("name") not in allowed:
                continue
            arguments = item.get("arguments", {})
            result.append(PlannedToolCall(
                name=str(item["name"]),
                arguments=arguments if isinstance(arguments, dict) else {},
                reason=str(item.get("reason", "")),
            ))
        return result
