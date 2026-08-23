"""Company-agnostic lead lifecycle automation contracts."""

from __future__ import annotations

from dataclasses import dataclass

from app.services.lead_service import ALLOWED_STATUSES, LeadService


@dataclass(frozen=True)
class LeadLifecycleResult:
    lead_id: int | None
    from_status: str | None
    to_status: str
    changed: bool


class LeadLifecycleService:
    """Apply validated lifecycle transitions inside one organization."""

    ORDER = {status: index for index, status in enumerate((
        "new", "contacted", "qualified", "converted", "lost"
    ))}

    def __init__(self, lead_service: LeadService) -> None:
        self.lead_service = lead_service

    def transition(self, *, lead_id: int, organization_id: int, target_status: str) -> LeadLifecycleResult:
        if target_status not in ALLOWED_STATUSES:
            raise ValueError(f"Invalid lead status: {target_status}")

        lead = self.lead_service.get_lead(lead_id, organization_id)
        if lead is None:
            return LeadLifecycleResult(None, None, target_status, False)

        current = lead.status
        if current == target_status:
            return LeadLifecycleResult(lead.id, current, target_status, False)

        self._validate_transition(current, target_status)
        updated = self.lead_service.update_status(lead.id, organization_id, target_status)
        return LeadLifecycleResult(
            updated.id if updated else None,
            current,
            target_status,
            updated is not None,
        )

    def _validate_transition(self, current: str, target: str) -> None:
        if current == "lost":
            raise ValueError("Lost leads cannot transition without explicit reactivation support")
        if target == "lost":
            return
        if self.ORDER[target] < self.ORDER[current]:
            raise ValueError(f"Invalid lifecycle transition: {current} -> {target}")
