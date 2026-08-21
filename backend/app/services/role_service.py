"""Organization-scoped role service."""

from sqlalchemy.orm import Session

from app.models.role import Role
from app.repositories.role_repository import RoleRepository


class RoleService:
    """Business logic for organization-scoped roles."""

    def __init__(self, db: Session):
        self.repository = RoleRepository(db)
        self.db = db

    def get_role(
        self,
        role_id: int,
        organization_id: int,
    ) -> Role | None:
        return self.repository.get_by_id_in_organization(
            role_id,
            organization_id,
        )

    def get_all_roles(
        self,
        organization_id: int,
    ) -> list[Role]:
        return self.repository.get_all_in_organization(
            organization_id
        )

    def get_role_by_name(
        self,
        name: str,
        organization_id: int,
    ) -> Role | None:
        return self.repository.get_by_name_in_organization(
            name.strip(),
            organization_id,
        )
