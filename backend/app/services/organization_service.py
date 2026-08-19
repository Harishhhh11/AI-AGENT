"""
Organization business logic.
"""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.exceptions.organization import (
    OrganizationAlreadyExistsException,
)
from app.models.organization import Organization
from app.repositories.organization_repository import (
    OrganizationRepository,
)
from app.schemas.organization import OrganizationCreate


class OrganizationService:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db
        self.repository = OrganizationRepository(db)

    def create_organization(
        self,
        organization: OrganizationCreate,
    ) -> Organization:

        if self.repository.get_by_email(
            organization.email
        ):
            raise OrganizationAlreadyExistsException(
                "email"
            )

        if self.repository.get_by_name(
            organization.name
        ):
            raise OrganizationAlreadyExistsException(
                "name"
            )

        db_organization = Organization(
            name=organization.name,
            email=organization.email,
        )

        try:

            return self.repository.create(
                db_organization
            )

        except IntegrityError:

            self.db.rollback()
            raise

    def get_organization(
        self,
        organization_id: int,
    ) -> Organization | None:

        return self.repository.get_by_id(
            organization_id
        )

    def update_organization(
        self,
        organization_id: int,
        organization: OrganizationCreate,
    ) -> Organization | None:

        db_organization = (
            self.repository.get_by_id(
                organization_id
            )
        )

        if db_organization is None:
            return None

        existing_email = (
            self.repository.get_by_email(
                organization.email
            )
        )

        if (
            existing_email is not None
            and existing_email.id != organization_id
        ):
            raise OrganizationAlreadyExistsException(
                "email"
            )

        existing_name = (
            self.repository.get_by_name(
                organization.name
            )
        )

        if (
            existing_name is not None
            and existing_name.id != organization_id
        ):
            raise OrganizationAlreadyExistsException(
                "name"
            )

        db_organization.name = organization.name
        db_organization.email = organization.email

        return self.repository.update(
            db_organization
        )

    def delete_organization(
        self,
        organization_id: int,
    ) -> bool:

        organization = (
            self.repository.get_by_id(
                organization_id
            )
        )

        if organization is None:
            return False

        self.repository.delete(
            organization
        )

        return True