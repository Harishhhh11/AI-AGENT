"""Organization-scoped role repository."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.role import Role
from app.repositories.base_repository import BaseRepository


class RoleRepository(BaseRepository[Role]):
    def __init__(self, db: Session):
        super().__init__(db, Role)

    def get_by_id_in_organization(
        self,
        role_id: int,
        organization_id: int,
    ) -> Role | None:
        statement = (
            select(Role)
            .where(Role.id == role_id)
            .where(Role.organization_id == organization_id)
        )
        return self.db.scalar(statement)

    def get_all_in_organization(
        self,
        organization_id: int,
    ) -> list[Role]:
        statement = (
            select(Role)
            .where(Role.organization_id == organization_id)
            .order_by(Role.id.asc())
        )
        return list(self.db.scalars(statement).all())

    def get_by_name_in_organization(
        self,
        name: str,
        organization_id: int,
    ) -> Role | None:
        statement = (
            select(Role)
            .where(Role.name == name)
            .where(Role.organization_id == organization_id)
        )
        return self.db.scalar(statement)
