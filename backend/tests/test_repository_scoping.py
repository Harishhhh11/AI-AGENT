from app.repositories.conversation_repository import ConversationRepository
from app.repositories.knowledge_repository import KnowledgeRepository
from app.repositories.lead_repository import LeadRepository


class CaptureDB:
    def __init__(self) -> None:
        self.statement = None

    def scalar(self, statement):
        self.statement = statement
        return None

    def scalars(self, statement):
        self.statement = statement

        class Result:
            def all(self):
                return []

        return Result()

    def execute(self, statement):
        self.statement = statement

        class Result:
            def all(self):
                return []

        return Result()


def statement_text(repo, method_name: str, *args) -> str:
    db = CaptureDB()
    repo.db = db
    getattr(repo, method_name)(*args)
    assert db.statement is not None
    return str(db.statement)


def test_conversation_id_lookup_is_tenant_scoped() -> None:
    repo = object.__new__(ConversationRepository)
    text = statement_text(repo, "get_by_id_in_organization", 10, 20)

    assert "conversations.id" in text
    assert "conversations.organization_id" in text


def test_knowledge_id_lookup_is_tenant_scoped() -> None:
    repo = object.__new__(KnowledgeRepository)
    text = statement_text(repo, "get_by_id_in_organization", 10, 20)

    assert "knowledge_base.id" in text
    assert "knowledge_base.organization_id" in text


def test_lead_id_lookup_is_tenant_scoped() -> None:
    repo = object.__new__(LeadRepository)
    text = statement_text(repo, "get_by_id_in_organization", 10, 20)

    assert "leads.id" in text
    assert "leads.organization_id" in text
