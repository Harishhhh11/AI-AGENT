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

Knowledge is always restricted to the current organization and, when supplied,
the active receptionist. Retrieval is hybrid: lexical matches provide precise
subject control and semantic search handles natural-language paraphrases.
"""

from __future__ import annotations

import re

from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.knowledge_base import KnowledgeBase
from app.repositories.knowledge_repository import KnowledgeRepository
from app.services.embedding_service import EmbeddingService


class KnowledgeService:
    DEFAULT_SEARCH_LIMIT = 5
    MAX_SEARCH_LIMIT = 10
    CANDIDATE_LIMIT = 20
    MAX_COSINE_DISTANCE = 0.55
    MAX_KEYWORDS = 8

    STOP_WORDS = {
        "a", "an", "and", "are", "am", "be", "can", "could", "do", "does", "did",
        "for", "from", "how", "i", "in", "is", "it", "me", "may", "my", "of", "on",
        "or", "please", "tell", "the", "their", "there", "this", "to", "we", "what",
        "when", "where", "which", "who", "why", "would", "you", "your", "about", "offer",
        "offers", "offering", "provide", "provides", "provided", "course", "courses", "class",
        "classes", "details", "information", "know", "want", "like", "need", "interested",
        "give", "get", "have", "has", "had", "much", "many", "fee", "fees", "price",
        "pricing", "cost", "costs", "training", "service", "services", "product", "products",
        "program", "programs", "available", "availability", "online", "offline", "classroom",
        "mode", "duration", "timing", "timings", "schedule", "topics", "topic", "covered",
        "cover", "syllabus", "contact", "phone", "email", "address", "location", "admission",
        "admissions", "registration", "enrollment", "enrolment", "batch", "started", "start",
        "everything", "complete", "full", "company", "business", "organization",
    }

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = KnowledgeRepository(db)
        self.embedding_service = EmbeddingService()

    def create(
        self,
        organization_id: int,
        title: str,
        content: str,
        source: str,
        category: str,
        agent_id: int | None = None,
    ) -> KnowledgeBase:
        title = (title or "").strip()
        content = (content or "").strip()
        source = (source or "manual").strip()
        category = (category or "general").strip()
        if not title:
            raise ValueError("Knowledge title cannot be empty.")
        if not content:
            raise ValueError("Knowledge content cannot be empty.")
        embedding = self.embedding_service.generate(
            self._build_embedding_text(title, content, category)
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
        result = self.repository.add(knowledge)
        self.db.commit()
        self.db.refresh(result)
        return result

    def get_all(self, organization_id: int) -> list[KnowledgeBase]:
        return self.repository.get_all_by_organization(organization_id)

    def get_by_id(self, knowledge_id: int, organization_id: int) -> KnowledgeBase | None:
        return self.repository.get_by_id_in_organization(knowledge_id, organization_id)

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
        knowledge = self.get_by_id(knowledge_id, organization_id)
        if knowledge is None:
            return None
        final_title = title.strip() if title is not None else knowledge.title
        final_content = content.strip() if content is not None else knowledge.content
        final_category = category.strip() if category is not None else knowledge.category
        if not final_title:
            raise ValueError("Knowledge title cannot be empty.")
        if not final_content:
            raise ValueError("Knowledge content cannot be empty.")
        knowledge.title = final_title
        knowledge.content = final_content
        knowledge.category = final_category
        if source is not None:
            knowledge.source = source.strip()
        if is_active is not None:
            knowledge.is_active = is_active
        if title is not None or content is not None or category is not None:
            knowledge.embedding = self.embedding_service.generate(
                self._build_embedding_text(final_title, final_content, final_category)
            )
        self.db.commit()
        self.db.refresh(knowledge)
        return knowledge

    def delete(self, knowledge_id: int, organization_id: int) -> bool:
        knowledge = self.get_by_id(knowledge_id, organization_id)
        if knowledge is None:
            return False
        self.db.delete(knowledge)
        self.db.commit()
        return True

    def deactivate(self, knowledge_id: int, organization_id: int) -> KnowledgeBase | None:
        knowledge = self.get_by_id(knowledge_id, organization_id)
        if knowledge is None:
            return None
        knowledge.is_active = False
        self.db.commit()
        self.db.refresh(knowledge)
        return knowledge

    def search(
        self,
        organization_id: int,
        query: str,
        limit: int = DEFAULT_SEARCH_LIMIT,
        agent_id: int | None = None,
    ) -> list[KnowledgeBase]:
        query = (query or "").strip()
        if not query or organization_id is None:
            return []
        try:
            limit = max(1, min(int(limit), self.MAX_SEARCH_LIMIT))
        except (TypeError, ValueError):
            limit = self.DEFAULT_SEARCH_LIMIT

        keywords = self._extract_keywords(query)
        keyword_results = self._keyword_search(organization_id, agent_id, keywords, self.CANDIDATE_LIMIT)
        if keyword_results:
            return self._rank_keyword_results(query, keyword_results, limit)

        return self._semantic_search(organization_id, agent_id, query, limit)

    def _keyword_search(
        self,
        organization_id: int,
        agent_id: int | None,
        keywords: list[str],
        limit: int,
    ) -> list[KnowledgeBase]:
        if not keywords:
            return []
        conditions = []
        for keyword in keywords:
            pattern = f"%{keyword}%"
            conditions.extend(
                (
                    func.lower(KnowledgeBase.title).like(pattern),
                    func.lower(KnowledgeBase.content).like(pattern),
                    func.lower(KnowledgeBase.category).like(pattern),
                )
            )
        statement = (
            select(KnowledgeBase)
            .where(KnowledgeBase.organization_id == organization_id)
            .where(KnowledgeBase.is_active.is_(True))
            .where(or_(*conditions))
            .order_by(KnowledgeBase.id.desc())
            .limit(limit)
        )
        if agent_id is not None:
            statement = statement.where(
                or_(KnowledgeBase.agent_id.is_(None), KnowledgeBase.agent_id == agent_id)
            )
        try:
            return list(self.db.scalars(statement).all())
        except Exception as exc:
            print("Keyword knowledge search error:", exc)
            return []

    def _rank_keyword_results(self, query: str, results: list[KnowledgeBase], limit: int) -> list[KnowledgeBase]:
        query_terms = [term for term in self._extract_keywords(query) if term not in self.STOP_WORDS]

        def score(item: KnowledgeBase) -> tuple[float, int]:
            title = self._normalize_text(item.title)
            content = self._normalize_text(item.content)
            category = self._normalize_text(item.category)
            if not query_terms:
                value = 0.0
            else:
                matched = sum(1 for term in query_terms if self._term_in_text(term, title + " " + content + " " + category))
                title_hits = sum(1 for term in query_terms if self._term_in_text(term, title))
                value = (matched / len(query_terms)) + (0.5 * title_hits / len(query_terms))
            return value, -(item.id or 0)

        return sorted(results, key=score, reverse=True)[:limit]

    def _semantic_search(
        self,
        organization_id: int,
        agent_id: int | None,
        query: str,
        limit: int,
    ) -> list[KnowledgeBase]:
        try:
            query_embedding = self.embedding_service.generate(query)
        except Exception as exc:
            print("Embedding generation error:", exc)
            return []
        distance = KnowledgeBase.embedding.cosine_distance(query_embedding)
        statement = (
            select(KnowledgeBase, distance.label("similarity_distance"))
            .where(KnowledgeBase.organization_id == organization_id)
            .where(KnowledgeBase.is_active.is_(True))
            .where(KnowledgeBase.embedding.is_not(None))
            .order_by(distance.asc())
            .limit(self.CANDIDATE_LIMIT)
        )
        if agent_id is not None:
            statement = statement.where(
                or_(KnowledgeBase.agent_id.is_(None), KnowledgeBase.agent_id == agent_id)
            )
        try:
            rows = self.db.execute(statement).all()
        except Exception as exc:
            print("Semantic knowledge search error:", exc)
            return []

        relevant = []
        for knowledge, raw_distance in rows:
            try:
                similarity_distance = float(raw_distance)
            except (TypeError, ValueError):
                continue
            if similarity_distance <= self.MAX_COSINE_DISTANCE:
                relevant.append(knowledge)
            if len(relevant) >= limit:
                break
        return relevant

    @classmethod
    def _extract_keywords(cls, query: str) -> list[str]:
        words = re.findall(r"[a-zA-Z0-9+#.-]+", (query or "").lower())
        keywords = []
        for word in words:
            word = word.strip(".-")
            if not word or len(word) < 2 or word in cls.STOP_WORDS:
                continue
            if word not in keywords:
                keywords.append(word)
        return keywords[: cls.MAX_KEYWORDS]

    @staticmethod
    def _term_in_text(term: str, text: str) -> bool:
        return bool(re.search(rf"(?<![a-zA-Z0-9+#]){re.escape(term.lower())}(?![a-zA-Z0-9+#])", text.lower()))

    @staticmethod
    def _normalize_text(text: str) -> str:
        return " ".join(str(text or "").lower().split())

    @staticmethod
    def _build_embedding_text(title: str, content: str, category: str) -> str:
        return f"TITLE:\n{title}\n\nCATEGORY:\n{category}\n\nCONTENT:\n{content}".strip()
