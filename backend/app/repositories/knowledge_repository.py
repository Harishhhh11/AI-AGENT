"""
Repository for knowledge base records.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.knowledge_base import KnowledgeBase
from app.repositories.base_repository import BaseRepository


class KnowledgeRepository(BaseRepository[KnowledgeBase]):
    """
    Database operations for knowledge base records.
    """

    def __init__(
        self,
        db: Session,
    ):
        super().__init__(
            db=db,
            model=KnowledgeBase,
        )

    def get_by_id(
        self,
        knowledge_id: int,
    ) -> KnowledgeBase | None:

        statement = (
            select(KnowledgeBase)
            .where(
                KnowledgeBase.id == knowledge_id
            )
        )

        return self.db.scalar(statement)

    def get_by_id_in_organization(
        self,
        knowledge_id: int,
        organization_id: int,
    ) -> KnowledgeBase | None:

        statement = (
            select(KnowledgeBase)
            .where(
                KnowledgeBase.id == knowledge_id
            )
            .where(
                KnowledgeBase.organization_id
                == organization_id
            )
        )

        return self.db.scalar(statement)

    def get_all(
        self,
        organization_id: int,
    ) -> list[KnowledgeBase]:

        statement = (
            select(KnowledgeBase)
            .where(
                KnowledgeBase.organization_id
                == organization_id
            )
            .order_by(
                KnowledgeBase.id.desc()
            )
        )

        return list(
            self.db.scalars(
                statement
            ).all()
        )

    def get_all_by_organization(
        self,
        organization_id: int,
    ) -> list[KnowledgeBase]:

        return self.get_all(
            organization_id
        )

    def search(
        self,
        organization_id: int,
        query_embedding: list[float],
        limit: int = 5,
    ) -> list[tuple[KnowledgeBase, float]]:
        """
        Semantic search using pgvector.
        """

        distance = (
            KnowledgeBase.embedding.cosine_distance(
                query_embedding
            )
        )

        statement = (
            select(
                KnowledgeBase,
                distance.label("distance"),
            )
            .where(
                KnowledgeBase.organization_id
                == organization_id
            )
            .where(
                KnowledgeBase.embedding.is_not(None)
            )
            .where(
                KnowledgeBase.is_active.is_(True)
            )
            .order_by(distance)
            .limit(limit)
        )

        rows = self.db.execute(
            statement
        ).all()

        return [
            (
                knowledge,
                float(distance_value),
            )
            for knowledge, distance_value in rows
        ]