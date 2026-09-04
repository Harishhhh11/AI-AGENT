"""Business rules for publishable AI receptionists."""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.agent import Agent
from app.repositories.agent_repository import AgentRepository
from app.schemas.agent import AgentCreate, AgentUpdate


class AgentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = AgentRepository(db)

    def create(self, organization_id: int, data: AgentCreate) -> Agent:
        public_slug = data.public_slug.strip().lower()
        if self.repository.get_by_slug(public_slug):
            raise ValueError("That public URL is already in use. Choose another slug.")

        agent = Agent(
            organization_id=organization_id,
            name=data.name.strip(),
            public_slug=public_slug,
            welcome_message=data.welcome_message.strip(),
            system_instructions=(data.system_instructions or "").strip() or None,
        )
        self.repository.add(agent)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("That public URL is already in use. Choose another slug.") from exc
        self.db.refresh(agent)
        return agent

    def get(self, agent_id: int, organization_id: int) -> Agent | None:
        return self.repository.get_by_id_in_organization(agent_id, organization_id)

    def get_all(self, organization_id: int) -> list[Agent]:
        return self.repository.get_all_in_organization(organization_id)

    def get_public(self, public_slug: str) -> Agent | None:
        agent = self.repository.get_by_slug(public_slug.strip().lower())
        if (
            not agent
            or not agent.is_active
            or not agent.is_published
            or not agent.organization
            or not agent.organization.is_active
        ):
            return None
        return agent

    def update(
        self, agent_id: int, organization_id: int, data: AgentUpdate
    ) -> Agent | None:
        agent = self.get(agent_id, organization_id)
        if not agent:
            return None
        for field in ("name", "welcome_message", "system_instructions", "is_active"):
            value = getattr(data, field)
            if value is not None:
                setattr(agent, field, value.strip() if isinstance(value, str) else value)
        self.db.commit()
        self.db.refresh(agent)
        return agent

    def set_published(
        self, agent_id: int, organization_id: int, is_published: bool
    ) -> Agent | None:
        agent = self.get(agent_id, organization_id)
        if not agent:
            return None
        agent.is_published = is_published
        self.db.commit()
        self.db.refresh(agent)
        return agent
