"""
Regenerate embeddings for all knowledge-base records.

Run this after changing the embedding strategy.

Usage:

python -m app.scripts.regenerate_knowledge_embeddings
"""

from sqlalchemy import select

from app.database.session import SessionLocal
from app.models.knowledge_base import KnowledgeBase
from app.services.embedding_service import EmbeddingService


def build_embedding_text(
    knowledge: KnowledgeBase,
) -> str:
    """
    Build the same embedding text used by KnowledgeService.
    """

    return f"""
TITLE:
{knowledge.title}

CATEGORY:
{knowledge.category}

CONTENT:
{knowledge.content}
""".strip()


def regenerate_embeddings() -> None:

    db = SessionLocal()

    try:

        embedding_service = (
            EmbeddingService()
        )

        statement = (
            select(KnowledgeBase)
            .order_by(
                KnowledgeBase.id.asc()
            )
        )

        knowledge_items = (
            db.scalars(
                statement
            ).all()
        )

        total = len(
            knowledge_items
        )

        print(
            "\n"
            "=========================================="
        )

        print(
            "KNOWLEDGE EMBEDDING REGENERATION"
        )

        print(
            "=========================================="
        )

        print(
            f"Records found: {total}"
        )

        print()

        if not knowledge_items:

            print(
                "No knowledge records found."
            )

            return

        for index, knowledge in enumerate(
            knowledge_items,
            start=1,
        ):

            print(
                f"[{index}/{total}] "
                f"Processing: "
                f"{knowledge.title}"
            )

            embedding_text = (
                build_embedding_text(
                    knowledge
                )
            )

            embedding = (
                embedding_service.generate(
                    embedding_text
                )
            )

            knowledge.embedding = (
                embedding
            )

        db.commit()

        print()

        print(
            "=========================================="
        )

        print(
            "Embedding regeneration completed."
        )

        print(
            f"Updated records: {total}"
        )

        print(
            "=========================================="
        )

    except Exception as exc:

        db.rollback()

        print()

        print(
            "Embedding regeneration failed:"
        )

        print(
            exc
        )

        raise

    finally:

        db.close()


if __name__ == "__main__":

    regenerate_embeddings()