import pytest

from app.services.business_action_service import BusinessActionService
from app.services.provider_execution_service import ProviderExecutionService


class FakeFollowUpProvider:
    name = "fake-follow-up"

    def supports(self, action_type: str) -> bool:
        return action_type == "lead_follow_up"

    async def execute(self, action):
        return "queued"


class FailingProvider(FakeFollowUpProvider):
    name = "failing-provider"

    async def execute(self, action):
        raise RuntimeError("provider unavailable")


@pytest.mark.asyncio
async def test_unconfigured_provider_is_blocked_safely():
    service = ProviderExecutionService()
    action = BusinessActionService().build_action(
        action_type="lead_follow_up",
        organization_id=1,
        lead_id=12,
        payload={"channel": "email"},
    )

    result = await service.execute(action)

    assert result.executed is False
    assert result.error == "provider_not_configured"
    assert result.action.status == "failed"


@pytest.mark.asyncio
async def test_configured_provider_executes_and_marks_completed():
    service = ProviderExecutionService(providers=[FakeFollowUpProvider()])
    action = BusinessActionService().build_action(
        action_type="lead_follow_up",
        organization_id=1,
        lead_id=12,
        payload={"channel": "email"},
    )

    result = await service.execute(action)

    assert result.executed is True
    assert result.provider == "fake-follow-up"
    assert result.action.status == "completed"
    assert result.action.payload["provider_result"] == "queued"


@pytest.mark.asyncio
async def test_provider_failure_is_structured():
    service = ProviderExecutionService(providers=[FailingProvider()])
    action = BusinessActionService().build_action(
        action_type="lead_follow_up",
        organization_id=1,
        lead_id=12,
    )

    result = await service.execute(action)

    assert result.executed is False
    assert result.provider == "failing-provider"
    assert result.error == "provider_execution_failed"
    assert result.action.status == "failed"
    assert "provider unavailable" in result.action.payload["error"]
