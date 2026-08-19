"""
Organization repository.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.repositories.base_repository import BaseRepository


class OrganizationRepository(
    BaseRepository[Organization]
):

    def __init__(self, db: Session):

        super().__init__(
            db=db,
            model=Organization,
        )

    def exists_by_email(
        self,
        email: str,
    ) -> bool:

        statement = select(Organization.id).where(
            Organization.email == email
        )

        return self.db.scalar(statement) is not None

    def exists_by_name(
        self,
        name: str,
    ) -> bool:

        statement = select(Organization.id).where(
            Organization.name == name
        )

        return self.db.scalar(statement) is not None

    def get_by_id(
        self,
        organization_id: int,
    ) -> Organization | None:

        statement = select(
            Organization
        ).where(
            Organization.id == organization_id
        )

        return self.db.scalar(statement)

    def get_all(self) -> list[Organization]:

        statement = select(
            Organization
        ).order_by(
            Organization.id.desc()
        )

        return list(
            self.db.scalars(statement).all()
        )