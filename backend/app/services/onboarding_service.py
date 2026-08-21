"""Transactional company onboarding service."""

from sqlalchemy.orm import Session

from app.auth.hashing import hash_password
from app.models.agent import Agent
from app.models.organization import Organization
from app.models.user import User
from app.repositories.agent_repository import AgentRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.user_repository import UserRepository
from app.schemas.onboarding import OnboardingRequest


class OnboardingService:
    """Create an organization, its first admin, and default agent atomically."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.organizations = OrganizationRepository(db)
        self.users = UserRepository(db)
        self.agents = AgentRepository(db)

    def onboard(self, data: OnboardingRequest) -> tuple[Organization, User, Agent]:
        organization_name = data.organization_name.strip()
        organization_email = str(data.organization_email).lower()
        admin_email = str(data.admin_email).lower()

        if self.organizations.get_by_name(organization_name):
            raise ValueError("An organization with this name already exists.")

        if self.organizations.get_by_email(organization_email):
            raise ValueError("An organization with this email already exists.")

        if self.users.get_by_email(admin_email):
            raise ValueError("A user with this email already exists.")

        public_slug = data.public_slug.strip().lower()
        if self.agents.get_by_slug(public_slug):
            raise ValueError("That public agent URL is already in use.")

        try:
            organization = Organization(
                name=organization_name,
                email=organization_email,
            )
            self.db.add(organization)
            self.db.flush()

            admin = User(
                organization_id=organization.id,
                first_name=data.first_name.strip(),
                last_name=data.last_name.strip(),
                email=admin_email,
                phone=data.phone.strip() if data.phone else None,
                password_hash=hash_password(data.password),
                is_verified=False,
                is_superuser=True,
            )
            self.db.add(admin)

            agent = Agent(
                organization_id=organization.id,
                name=data.agent_name.strip(),
                public_slug=public_slug,
                welcome_message="Hello! How can I help you today?",
                system_instructions=None,
                is_published=False,
            )
            self.db.add(agent)

            self.db.commit()
            self.db.refresh(organization)
            self.db.refresh(admin)
            self.db.refresh(agent)

            return organization, admin, agent

        except Exception:
            self.db.rollback()
            raise
