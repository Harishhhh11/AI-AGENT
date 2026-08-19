"""
Knowledge base service.

Handles:

- Creating knowledge
- Updating knowledge
- Deleting knowledge
- Retrieving knowledge
- Organization-scoped semantic search
- Keyword/exact-match retrieval
- Relevance filtering

This service is completely company-agnostic.

IMPORTANT:

Knowledge is ALWAYS restricted to the current organization.

The service never intentionally falls back to another
organization's knowledge.

Retrieval uses a hybrid strategy:

    1. Keyword / exact subject matching
    2. Semantic vector search
    3. Relevance filtering

This prevents cases where:

    Customer asks about Java
            ↓
    Java does not exist
            ↓
    Semantic search finds Python
            ↓
    AI incorrectly answers about Python

Instead:

    Customer asks about Java
            ↓
    No Java knowledge
            ↓
    Return []
            ↓
    AI honestly says information is unavailable.
"""

import re

from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.knowledge_base import KnowledgeBase
from app.repositories.knowledge_repository import (
    KnowledgeRepository,
)
from app.services.embedding_service import (
    EmbeddingService,
)


class KnowledgeService:
    """
    Service responsible for knowledge-base operations
    and reliable company knowledge retrieval.
    """

    # =========================================================
    # SEARCH SETTINGS
    # =========================================================

    DEFAULT_SEARCH_LIMIT = 5

    MAX_SEARCH_LIMIT = 10

    # Number of semantic candidates retrieved before filtering.
    CANDIDATE_LIMIT = 20

    # Maximum cosine distance accepted for semantic matches.
    #
    # Lower = stricter.
    #
    # We use semantic search only when keyword retrieval does
    # not already identify the requested subject.
    MAX_COSINE_DISTANCE = 0.55

    # Maximum number of keywords used in SQL keyword search.
    MAX_KEYWORDS = 8

    # =========================================================
    # GENERIC STOP WORDS
    # =========================================================
    #
    # These are NOT company-specific.
    #
    # They prevent words such as:
    #
    # "what"
    # "is"
    # "the"
    # "how"
    #
    # from becoming the main retrieval signal.
    #
    # The actual subject words such as:
    #
    # python
    # java
    # web
    # machine
    # learning
    #
    # remain.
    # =========================================================

    STOP_WORDS = {
        "a",
        "an",
        "and",
        "are",
        "am",
        "be",
        "can",
        "could",
        "do",
        "does",
        "did",
        "for",
        "from",
        "how",
        "i",
        "in",
        "is",
        "it",
        "me",
        "may",
        "my",
        "of",
        "on",
        "or",
        "please",
        "tell",
        "the",
        "their",
        "there",
        "this",
        "to",
        "we",
        "what",
        "when",
        "where",
        "which",
        "who",
        "why",
        "would",
        "you",
        "your",
        "about",
        "offer",
        "offers",
        "offering",
        "provide",
        "provides",
        "provided",
        "course",
        "courses",
        "class",
        "classes",
        "details",
        "information",
        "know",
        "want",
        "like",
        "need",
        "interested",
        "give",
        "get",
        "have",
        "has",
        "had",
        "please",
        "much",
        "many",
        "fee",
        "fees",
        "price",
        "pricing",
        "cost",
        "costs",
    }

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(
        self,
        db: Session,
    ) -> None:

        self.db = db

        self.repository = (
            KnowledgeRepository(db)
        )

        self.embedding_service = (
            EmbeddingService()
        )

    # =========================================================
    # CREATE
    # =========================================================

    def create(
        self,
        organization_id: int,
        title: str,
        content: str,
        source: str,
        category: str,
        agent_id: int | None = None,
    ) -> KnowledgeBase:
        """
        Create a knowledge record and generate its embedding.
        """

        title = (
            title or ""
        ).strip()

        content = (
            content or ""
        ).strip()

        source = (
            source or "manual"
        ).strip()

        category = (
            category or "general"
        ).strip()

        if not title:

            raise ValueError(
                "Knowledge title cannot be empty."
            )

        if not content:

            raise ValueError(
                "Knowledge content cannot be empty."
            )

        embedding_text = (
            self._build_embedding_text(
                title=title,
                content=content,
                category=category,
            )
        )

        embedding = (
            self.embedding_service.generate(
                embedding_text
            )
        )

        knowledge = KnowledgeBase(
            organization_id=organization_id,
            agent_id=agent_id,
            title=title,
            content=content,
            source=source,
            category=category,
            embedding=embedding,
        )

        result = (
            self.repository.add(
                knowledge
            )
        )

        self.db.commit()

        self.db.refresh(
            result
        )

        return result

    # =========================================================
    # GET ALL
    # =========================================================

    def get_all(
        self,
        organization_id: int,
    ) -> list[KnowledgeBase]:

        return (
            self.repository
            .get_all_by_organization(
                organization_id
            )
        )

    # =========================================================
    # GET BY ID
    # =========================================================

    def get_by_id(
        self,
        knowledge_id: int,
        organization_id: int,
    ) -> KnowledgeBase | None:

        return (
            self.repository
            .get_by_id_in_organization(
                knowledge_id,
                organization_id,
            )
        )

    # =========================================================
    # UPDATE
    # =========================================================

    def update(
        self,
        knowledge_id: int,
        organization_id: int,
        title: str | None = None,
        content: str | None = None,
        source: str | None = None,
        category: str | None = None,
        is_active: bool | None = None,
    ) -> KnowledgeBase | None:

        knowledge = (
            self.get_by_id(
                knowledge_id=knowledge_id,
                organization_id=organization_id,
            )
        )

        if knowledge is None:

            return None

        final_title = (
            title.strip()
            if title is not None
            else knowledge.title
        )

        final_content = (
            content.strip()
            if content is not None
            else knowledge.content
        )

        final_category = (
            category.strip()
            if category is not None
            else knowledge.category
        )

        if not final_title:

            raise ValueError(
                "Knowledge title cannot be empty."
            )

        if not final_content:

            raise ValueError(
                "Knowledge content cannot be empty."
            )

        # -----------------------------------------------------
        # Update fields
        # -----------------------------------------------------

        knowledge.title = final_title

        knowledge.content = final_content

        knowledge.category = final_category

        if source is not None:

            knowledge.source = (
                source.strip()
            )

        if is_active is not None:

            knowledge.is_active = (
                is_active
            )

        # -----------------------------------------------------
        # Regenerate embedding when semantic content changes.
        # -----------------------------------------------------

        if (
            title is not None
            or content is not None
            or category is not None
        ):

            embedding_text = (
                self._build_embedding_text(
                    title=final_title,
                    content=final_content,
                    category=final_category,
                )
            )

            knowledge.embedding = (
                self.embedding_service.generate(
                    embedding_text
                )
            )

        self.db.commit()

        self.db.refresh(
            knowledge
        )

        return knowledge

    # =========================================================
    # DELETE
    # =========================================================

    def delete(
        self,
        knowledge_id: int,
        organization_id: int,
    ) -> bool:

        knowledge = (
            self.get_by_id(
                knowledge_id=knowledge_id,
                organization_id=organization_id,
            )
        )

        if knowledge is None:

            return False

        self.db.delete(
            knowledge
        )

        self.db.commit()

        return True

    # =========================================================
    # DEACTIVATE
    # =========================================================

    def deactivate(
        self,
        knowledge_id: int,
        organization_id: int,
    ) -> KnowledgeBase | None:

        knowledge = (
            self.get_by_id(
                knowledge_id=knowledge_id,
                organization_id=organization_id,
            )
        )

        if knowledge is None:

            return None

        knowledge.is_active = False

        self.db.commit()

        self.db.refresh(
            knowledge
        )

        return knowledge

    # =========================================================
    # MAIN SEARCH
    # =========================================================

    def search(
        self,
        organization_id: int,
        query: str,
        limit: int = DEFAULT_SEARCH_LIMIT,
        agent_id: int | None = None,
    ) -> list[KnowledgeBase]:
        """
        Hybrid knowledge retrieval.

        Strategy:

            Query
              ↓
            Normalize
              ↓
            Keyword / exact matching
              ↓
            If strong keyword match exists:
                return keyword results
              ↓
            Otherwise:
                semantic vector search
              ↓
            Apply distance threshold
              ↓
            Return relevant knowledge only

        This is important because pure semantic search can
        incorrectly treat related subjects as equivalent.

        Example:

            Knowledge:
                Python course

            User:
                What about Java?

        Semantic search might think Python is related to
        programming.

        Hybrid search prevents that when there is no Java
        knowledge.
        """

        # =====================================================
        # 1. VALIDATE QUERY
        # =====================================================

        query = (
            query or ""
        ).strip()

        if not query:

            return []

        # =====================================================
        # 2. VALIDATE ORGANIZATION
        # =====================================================

        if organization_id is None:

            return []

        # =====================================================
        # 3. VALIDATE LIMIT
        # =====================================================

        try:

            limit = int(
                limit
            )

        except (
            TypeError,
            ValueError,
        ):

            limit = (
                self.DEFAULT_SEARCH_LIMIT
            )

        if limit <= 0:

            return []

        limit = min(
            limit,
            self.MAX_SEARCH_LIMIT,
        )

        # =====================================================
        # 4. EXTRACT SEARCH KEYWORDS
        # =====================================================

        keywords = (
            self._extract_keywords(
                query
            )
        )

        # =====================================================
        # 5. KEYWORD SEARCH
        # =====================================================

        keyword_results = (
            self._keyword_search(
                organization_id=organization_id,
                agent_id=agent_id,
                keywords=keywords,
                limit=limit,
            )
        )

        # -----------------------------------------------------
        # IMPORTANT:
        #
        # If keyword search finds a strong match, return it
        # immediately.
        #
        # This prevents unrelated semantic matches.
        # -----------------------------------------------------

        if keyword_results:

            print(
                "\n"
                "========== KNOWLEDGE SEARCH =========="
            )

            print(
                "Organization:",
                organization_id,
            )

            print(
                "Query:",
                query,
            )

            print(
                "Keywords:",
                keywords,
            )

            print(
                "Method:",
                "keyword",
            )

            print(
                "Results:",
                [
                    item.title
                    for item in keyword_results
                ],
            )

            print(
                "=======================================\n"
            )

            return keyword_results

        # =====================================================
        # 6. SEMANTIC SEARCH FALLBACK
        # =====================================================

        semantic_results = (
            self._semantic_search(
                organization_id=organization_id,
                agent_id=agent_id,
                query=query,
                limit=limit,
            )
        )

        print(
            "\n"
            "========== KNOWLEDGE SEARCH =========="
        )

        print(
            "Organization:",
            organization_id,
        )

        print(
            "Query:",
            query,
        )

        print(
            "Keywords:",
            keywords,
        )

        print(
            "Method:",
            "semantic",
        )

        print(
            "Results:",
            [
                item.title
                for item in semantic_results
            ],
        )

        print(
            "=======================================\n"
        )

        return semantic_results

    # =========================================================
    # KEYWORD SEARCH
    # =========================================================

    def _keyword_search(
        self,
        organization_id: int,
        agent_id: int | None,
        keywords: list[str],
        limit: int,
    ) -> list[KnowledgeBase]:
        """
        Search title/content using meaningful query terms.

        This is intentionally generic.

        It does NOT contain:

            Python
            Java
            Web Development
            Maruthi Technologies

        or any other company-specific information.

        The database determines what subjects exist.
        """

        if not keywords:

            return []

        # -----------------------------------------------------
        # Build SQL OR conditions.
        #
        # Example:
        #
        # query = "do you offer python"
        #
        # keywords = ["python"]
        #
        # Search:
        #
        # title ILIKE "%python%"
        # OR
        # content ILIKE "%python%"
        # -----------------------------------------------------

        conditions = []

        for keyword in keywords:

            pattern = (
                f"%{keyword}%"
            )

            conditions.append(
                func.lower(
                    KnowledgeBase.title
                ).like(
                    pattern
                )
            )

            conditions.append(
                func.lower(
                    KnowledgeBase.content
                ).like(
                    pattern
                )
            )

            conditions.append(
                func.lower(
                    KnowledgeBase.category
                ).like(
                    pattern
                )
            )

        if not conditions:

            return []

        statement = (
            select(
                KnowledgeBase
            )
            .where(
                KnowledgeBase.organization_id
                == organization_id
            )
            .where(
                KnowledgeBase.is_active.is_(True)
            )
            .where(
                or_(
                    *conditions
                )
            )
            .order_by(
                KnowledgeBase.id.desc()
            )
            .limit(
                limit
            )
        )

        if agent_id is not None:
            statement = statement.where(
                or_(
                    KnowledgeBase.agent_id.is_(None),
                    KnowledgeBase.agent_id == agent_id,
                )
            )

        try:

            results = (
                self.db.scalars(
                    statement
                ).all()
            )

        except Exception as exc:

            print(
                "Keyword knowledge search error:",
                exc,
            )

            return []

        return list(
            results
        )

    # =========================================================
    # SEMANTIC SEARCH
    # =========================================================

    def _semantic_search(
        self,
        organization_id: int,
        agent_id: int | None,
        query: str,
        limit: int,
    ) -> list[KnowledgeBase]:
        """
        Semantic vector search.

        Used only when direct keyword retrieval did not find
        anything.

        This allows natural-language questions such as:

            "Can I join remotely?"

        to find knowledge such as:

            "Online classes are available."

        without requiring exact word matches.
        """

        # -----------------------------------------------------
        # Generate query embedding
        # -----------------------------------------------------

        try:

            query_embedding = (
                self.embedding_service.generate(
                    query
                )
            )

        except Exception as exc:

            print(
                "Embedding generation error:",
                exc,
            )

            return []

        # -----------------------------------------------------
        # Calculate cosine distance
        # -----------------------------------------------------

        distance = (
            KnowledgeBase.embedding
            .cosine_distance(
                query_embedding
            )
        )

        # -----------------------------------------------------
        # Retrieve candidates
        # -----------------------------------------------------

        statement = (
            select(
                KnowledgeBase,
                distance.label(
                    "similarity_distance"
                ),
            )
            .where(
                KnowledgeBase.organization_id
                == organization_id
            )
            .where(
                KnowledgeBase.is_active.is_(True)
            )
            .where(
                KnowledgeBase.embedding.is_not(None)
            )
            .order_by(
                distance.asc()
            )
            .limit(
                self.CANDIDATE_LIMIT
            )
        )

        if agent_id is not None:
            statement = statement.where(
                or_(
                    KnowledgeBase.agent_id.is_(None),
                    KnowledgeBase.agent_id == agent_id,
                )
            )

        try:

            result = (
                self.db.execute(
                    statement
                )
            )

            rows = result.all()

        except Exception as exc:

            print(
                "Semantic knowledge search error:",
                exc,
            )

            return []

        relevant = []

        for row in rows:

            knowledge = row[0]

            raw_distance = row[1]

            try:

                similarity_distance = float(
                    raw_distance
                )

            except (
                TypeError,
                ValueError,
            ):

                continue

            print(
                f"Semantic candidate: "
                f"{knowledge.title} "
                f"| distance="
                f"{similarity_distance:.4f}"
            )

            if (
                similarity_distance
                <= self.MAX_COSINE_DISTANCE
            ):

                relevant.append(
                    knowledge
                )

            if len(
                relevant
            ) >= limit:

                break

        return relevant

    # =========================================================
    # KEYWORD EXTRACTION
    # =========================================================

    @classmethod
    def _extract_keywords(
        cls,
        query: str,
    ) -> list[str]:
        """
        Extract meaningful searchable terms.

        Example:

            "Do you offer Python courses?"

        becomes approximately:

            ["python"]

        Example:

            "What is the fee for Python?"

        becomes:

            ["python"]

        Example:

            "What about web development?"

        becomes:

            ["web", "development"]

        The method is generic and contains no company-specific
        subjects.
        """

        text = (
            query or ""
        ).lower()

        # -----------------------------------------------------
        # Keep words and numbers.
        # -----------------------------------------------------

        words = re.findall(
            r"[a-zA-Z0-9]+",
            text,
        )

        keywords = []

        for word in words:

            word = (
                word.strip()
            )

            if not word:

                continue

            if word in cls.STOP_WORDS:

                continue

            # Avoid extremely short noise words.
            if len(word) < 2:

                continue

            if word not in keywords:

                keywords.append(
                    word
                )

        return keywords[
            : cls.MAX_KEYWORDS
        ]

    # =========================================================
    # EMBEDDING TEXT
    # =========================================================

    @staticmethod
    def _build_embedding_text(
        title: str,
        content: str,
        category: str,
    ) -> str:
        """
        Build text used to generate the knowledge embedding.

        No company-specific information is hard-coded.
        """

        return f"""
TITLE:
{title}

CATEGORY:
{category}

CONTENT:
{content}
""".strip()
