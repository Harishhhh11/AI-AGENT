import asyncio

from app.tools.base import ToolContext
from app.tools.planner import ToolPlanner
from app.tools.registry import ToolRegistry


class FakeLLM:
    async def generate_structured(self, prompt: str) -> str:
        return '{"tool_calls":[{"name":"send_email","arguments":{"subject":"New lead"},"reason":"The customer asked to email the details."}]}'


def test_registry_contains_agent_tools():
    registry = ToolRegistry()
    names = {item["name"] for item in registry.descriptions()}
    assert {
        "save_lead",
        "google_sheet",
        "crm_sync",
        "send_email",
        "send_whatsapp",
        "book_appointment",
    } <= names


def test_planner_returns_only_allowlisted_tools():
    registry = ToolRegistry()
    calls = asyncio.run(ToolPlanner().decide(
        llm=FakeLLM(),
        context=ToolContext(db=None, organization_id=1, message="Please email me the details."),
        tool_descriptions=registry.descriptions(),
    ))
    assert len(calls) == 1
    assert calls[0].name == "send_email"
