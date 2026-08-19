"""
Role service.
"""

from sqlalchemy.orm import Session

from app.repositories.role_repository import RoleRepository


class RoleService:

    def __init__(
        self,
        db: Session,
    ):
        self.repository = RoleRepository(db)

    def get_role(
        self,
        role_id: int,
    ):
        return self.repository.get_by_id(role_id)

    def get_all_roles(self):
        return self.repository.get_all()

    def get_role_by_name(
        self,
        name: str,
    ):
        return self.repository.get_by_name(name)