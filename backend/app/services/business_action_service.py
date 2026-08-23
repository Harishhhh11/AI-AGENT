"""Audit-safe business action contracts for Phase 4 integrations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class BusinessAction:
    action_type: str
    organization_id: int
    lead_id: int | None
    payload: dict[str, Any]
    status: str = "pending"
    created_at: datetime = datetime.utcnow()


class BusinessActionService:
    """Create provider-neutral action records before external execution."""

    ALLOWED_ACTIONS = {
        "lead_follow_up",
        "crm_sync",
        "sheet_sync",
    }

    def build_action(
        self,
        *,
        action_type: str,
        organization_id: int,
        lead_id: int | None,
        payload: dict[str, Any] | None = None,
    ) -> BusinessAction:
        if action_type not in self.ALLOWED_ACTIONS:
            raise ValueError(f"Unsupported business action: {action_type}")
        if organization_id <= 0:
            raise ValueError("organization_id must be positive")
        return BusinessAction(
            action_type=action_type,
            organization_id=organization_id,
            lead_id=lead_id,
            payload=dict(payload or {}),
        )

    def mark_completed(self, action: BusinessAction) -> BusinessAction:
        return BusinessAction(
            action_type=action.action_type,
            organization_id=action.organization_id,
            lead_id=action.lead_id,
            payload=action.payload,
            status="completed",
            created_at=action.created_at,
        )

    def mark_failed(self, action: BusinessAction, error: str) -> BusinessAction:
        payload = dict(action.payload)
        payload["error"] = error
        return BusinessAction(
            action_type=action.action_type,
            organization_id=action.organization_id,
            lead_id=action.lead_id,
            payload=payload,
            status="failed",
            created_at=action.created_at,
        )
