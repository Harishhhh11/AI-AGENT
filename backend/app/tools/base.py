"""Contracts shared by every agent tool.

Tools are deliberately small and typed.  A tool can only receive the
organization and conversation context supplied by the server; the model
never gets direct access to a database session or arbitrary Python code.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session


@dataclass(slots=True)
class ToolContext:
    db: Session
    organization_id: int
    conversation_id: int | None = None
    user_id: int | None = None
    message: str = ""
    lead_context: Any | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ToolResult:
    tool_name: str
    success: bool
    message: str
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "error": self.error,
        }


class BaseTool(ABC):
    """A server-side action available to the agent."""

    name: str
    description: str
    requires_confirmation: bool = True

    @property
    @abstractmethod
    def input_schema(self) -> dict[str, Any]:
        """JSON-schema-like description used by the planner."""
        raise NotImplementedError

    @abstractmethod
    async def execute(
        self,
        context: ToolContext,
        arguments: dict[str, Any] | None = None,
    ) -> ToolResult:
        raise NotImplementedError
