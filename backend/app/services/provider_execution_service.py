"""Provider-neutral execution boundary for business actions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.services.business_action_service import BusinessAction, BusinessActionService


class BusinessActionProvider(Protocol):
    name: str

    def supports(self, action_type: str) -> bool:
        ...

    async def execute(self, action: BusinessAction) -> str:
        ...


@dataclass(frozen=True)
class ProviderExecutionResult:
    action: BusinessAction
    provider: str | None
    executed: bool
    error: str | None = None


class ProviderExecutionService:
    """Execute business actions only through explicitly registered providers."""

    def __init__(
        self,
        action_service: BusinessActionService | None = None,
        providers: list[BusinessActionProvider] | None = None,
    ) -> None:
        self.action_service = action_service or BusinessActionService()
        self.providers = list(providers or [])

    def register(self, provider: BusinessActionProvider) -> None:
        self.providers.append(provider)

    async def execute(self, action: BusinessAction) -> ProviderExecutionResult:
        provider = next(
            (item for item in self.providers if item.supports(action.action_type)),
            None,
        )
        if provider is None:
            return ProviderExecutionResult(
                action=self.action_service.mark_failed(
                    action,
                    "No provider configured for this business action.",
                ),
                provider=None,
                executed=False,
                error="provider_not_configured",
            )

        try:
            provider_result = await provider.execute(action)
            completed = self.action_service.mark_completed(action)
            return ProviderExecutionResult(
                action=BusinessAction(
                    action_type=completed.action_type,
                    organization_id=completed.organization_id,
                    lead_id=completed.lead_id,
                    payload={**completed.payload, "provider_result": provider_result},
                    status=completed.status,
                    created_at=completed.created_at,
                ),
                provider=provider.name,
                executed=True,
            )
        except Exception as exc:
            failed = self.action_service.mark_failed(action, str(exc))
            return ProviderExecutionResult(
                action=failed,
                provider=provider.name,
                executed=False,
                error="provider_execution_failed",
            )
