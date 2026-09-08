"""Business rules for publishable AI receptionists and their knowledge scope."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.agent import Agent
from app.models.knowledge_base import KnowledgeBase
from app.repositories.agent_repository import AgentRepository
from app.schemas.agent import AgentCreate, AgentUpdate


class AgentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = AgentRepository(db)

    @staticmethod
    def _knowledge_ids(agent: Agent) -> list[int]:
        return [
            int(item.id)
            for item in (agent.knowledge_items or [])
            if getattr(item, "is_active", False) and item.id is not None
        ]

    def create(self, organization_id: int, data: AgentCreate) -> Agent:
        public_slug = data.public_slug.strip().lower()
        if self.repository.get_by_slug(public_slug):
            raise ValueError("That public URL is already in use. Choose another slug.")

        selected_ids = list(dict.fromkeys(data.knowledge_item_ids or []))
        items = self._load_selected_items(organization_id, selected_ids)

        agent = Agent(
            organization_id=organization_id,
            name=data.name.strip(),
            public_slug=public_slug,
            welcome_message=data.welcome_message.strip(),
            system_instructions=(data.system_instructions or "").strip() or None,
        )
        self.repository.add(agent)
        try:
            self.db.flush()
            for item in items:
                if item.agent_id is not None:
                    raise ValueError(
                        f'"{item.title}" is already assigned to another receptionist. '
                        "Move it to shared scope before selecting it here."
                    )
                item.agent_id = agent.id
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("That public URL is already in use. Choose another slug.") from exc
        except ValueError:
            self.db.rollback()
            raise
        self.db.refresh(agent)
        return agent

    def get(self, agent_id: int, organization_id: int) -> Agent | None:
        return self.repository.get_by_id_in_organization(agent_id, organization_id)

    def get_all(self, organization_id: int) -> list[Agent]:
        return self.repository.get_all_in_organization(organization_id)

    def get_knowledge(self, agent_id: int, organization_id: int) -> list[KnowledgeBase] | None:
        agent = self.get(agent_id, organization_id)
        if not agent:
            return None
        return list(
            self.db.scalars(
                select(KnowledgeBase)
                .where(
                    KnowledgeBase.organization_id == organization_id,
                    KnowledgeBase.agent_id == agent_id,
                )
                .order_by(KnowledgeBase.id.desc())
            ).all()
        )

    def _load_selected_items(self, organization_id: int, selected_ids: list[int]) -> list[KnowledgeBase]:
        if not selected_ids:
            return []
        items = list(
            self.db.scalars(
                select(KnowledgeBase).where(
                    KnowledgeBase.organization_id == organization_id,
                    KnowledgeBase.id.in_(selected_ids),
                    KnowledgeBase.is_active.is_(True),
                )
            ).all()
        )
        found_ids = {int(item.id) for item in items}
        if any(item_id not in found_ids for item_id in selected_ids):
            raise ValueError("One or more selected knowledge items are not available in this organization.")
        return items

    def set_knowledge(
        self,
        agent_id: int,
        organization_id: int,
        knowledge_item_ids: list[int],
    ) -> Agent | None:
        agent = self.get(agent_id, organization_id)
        if not agent:
            return None

        selected_ids = list(dict.fromkeys(knowledge_item_ids or []))
        items = self._load_selected_items(organization_id, selected_ids)

        existing = list(
            self.db.scalars(
                select(KnowledgeBase).where(
                    KnowledgeBase.organization_id == organization_id,
                    KnowledgeBase.agent_id == agent_id,
                )
            ).all()
        )
        selected_set = set(selected_ids)
        for item in existing:
            if item.id not in selected_set:
                item.agent_id = None

        for item in items:
            if item.agent_id not in (None, agent_id):
                raise ValueError(
                    f'"{item.title}" is already assigned to another receptionist. '
                    "Reassign it from Knowledge Management first."
                )
            item.agent_id = agent_id

        self.db.commit()
        self.db.refresh(agent)
        return agent

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
        if is_published and not agent.is_active:
            raise ValueError("Activate this receptionist before publishing it.")
        agent.is_published = is_published
        self.db.commit()
        self.db.refresh(agent)
        return agent
