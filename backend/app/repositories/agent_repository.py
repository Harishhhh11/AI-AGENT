"""Organization-scoped queries for AI receptionists."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.agent import Agent
from app.repositories.base_repository import BaseRepository


class AgentRepository(BaseRepository[Agent]):
    def __init__(self, db: Session) -> None:
        super().__init__(db=db, model=Agent)

    def get_by_slug(self, public_slug: str) -> Agent | None:
        return self.db.scalar(
            select(Agent).where(Agent.public_slug == public_slug)
        )

    def get_by_id_in_organization(
        self, agent_id: int, organization_id: int
    ) -> Agent | None:
        return self.db.scalar(
            select(Agent)
            .where(Agent.id == agent_id)
            .where(Agent.organization_id == organization_id)
        )

    def get_all_in_organization(self, organization_id: int) -> list[Agent]:
        return list(
            self.db.scalars(
                select(Agent)
                .where(Agent.organization_id == organization_id)
                .order_by(Agent.created_at.desc())
            ).all()
        )
