"""
Tenant context.

Contains the organization and user associated
with the current authenticated request.
"""

from dataclasses import dataclass


@dataclass
class TenantContext:
    organization_id: int
    user_id: int