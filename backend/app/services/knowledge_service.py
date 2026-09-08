"""Knowledge base operations and tenant-safe hybrid retrieval."""

from __future__ import annotations

import re
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.knowledge_base import KnowledgeBase
from app.repositories.knowledge_repository import KnowledgeRepository
from app.services.embedding_service import EmbeddingService


_UNSET = object()


class KnowledgeService:
    DEFAULT_SEARCH_LIMIT = 5
    MAX_SEARCH_LIMIT = 10
    CANDIDATE_LIMIT = 25
    MAX_COSINE_DISTANCE = 0.68
    MAX_KEYWORDS = 8

    STOP_WORDS = {
        "a", "an", "and", "are", "am", "be", "can", "could", "do", "does", "did", "for", "from", "how", "i",
        "in", "is", "it", "me", "may", "my", "of", "on", "or", "please", "tell", "the", "their", "there",
        "this", "to", "we", "what", "when", "where", "which", "who", "why", "would", "you", "your", "about",
        "offer", "offers", "offering", "provide", "provides", "provided", "course", "courses", "class", "classes",
        "details", "information", "know", "want", "like", "need", "interested", "give", "get", "have", "has", "had",
        "much", "many", "fee", "fees", "price", "pricing", "cost", "costs", "training", "service", "services", "product",
        "products", "program", "programs", "available", "availability", "online", "offline", "classroom", "mode", "duration",
        "timing", "timings", "schedule", "topics", "topic", "covered", "cover", "syllabus", "contact", "phone", "email",
        "address", "location", "admission", "admissions", "registration", "enrollment", "enrolment", "batch", "started",
        "start", "everything", "complete", "full", "company", "business", "organization", "companies", "our",
    }

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = KnowledgeRepository(db)
        self.embedding_service = EmbeddingService()

    @staticmethod
    def _build_embedding_text(title: str, content: str, category: str) -> str:
        return f"TITLE:\n{title}\n\nCATEGORY:\n{category}\n\nCONTENT:\n{content}".strip()

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
        category = (category or "general").strip()
        if not title:
            raise ValueError("Knowledge title cannot be empty.")
        if not content:
            raise ValueError("Knowledge content cannot be empty.")
        knowledge = KnowledgeBase(
            organization_id=organization_id,
            agent_id=agent_id,
            title=title,
            content=content,
            source=(source or "manual").strip(),
            category=category,
            embedding=self.embedding_service.generate(self._build_embedding_text(title, content, category)),
        )
        result = self.repository.add(knowledge)
        self.db.commit()
        self.db.refresh(result)
        return result

    def get_all(self, organization_id: int, agent_id: int | None = None, scope: str = "all") -> list[KnowledgeBase]:
        statement = select(KnowledgeBase).where(KnowledgeBase.organization_id == organization_id).order_by(KnowledgeBase.id.desc())
        if scope == "shared":
            statement = statement.where(KnowledgeBase.agent_id.is_(None))
        elif scope == "agent":
            if agent_id is None:
                raise ValueError("agent_id is required for agent scope.")
            statement = statement.where(KnowledgeBase.agent_id == agent_id)
        elif scope == "available":
            if agent_id is None:
                raise ValueError("agent_id is required for available scope.")
            statement = statement.where(or_(KnowledgeBase.agent_id.is_(None), KnowledgeBase.agent_id == agent_id))
        return list(self.db.scalars(statement).all())

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
        agent_id: Any = _UNSET,
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
        if agent_id is not _UNSET:
            knowledge.agent_id = agent_id
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

    def search(self, organization_id: int, query: str, limit: int = DEFAULT_SEARCH_LIMIT, agent_id: int | None = None) -> list[KnowledgeBase]:
        query = (query or "").strip()
        if not query or organization_id is None:
            return []
        try:
            limit = max(1, min(int(limit), self.MAX_SEARCH_LIMIT))
        except (TypeError, ValueError):
            limit = self.DEFAULT_SEARCH_LIMIT

        keywords = self._extract_keywords(query)
        lexical = self._keyword_search(organization_id, agent_id, keywords, self.CANDIDATE_LIMIT)
        semantic = self._semantic_search(organization_id, agent_id, query, self.CANDIDATE_LIMIT)
        by_id: dict[int, KnowledgeBase] = {}
        for item in lexical + semantic:
            if getattr(item, "id", None) is not None:
                by_id[item.id] = item
        candidates = list(by_id.values())
        if not candidates:
            return []

        q_terms = set(keywords)
        normalized_query = self._normalize_text(query)

        def score(item: KnowledgeBase) -> tuple[float, float, int]:
            title = self._normalize_text(item.title)
            category = self._normalize_text(item.category)
            content = self._normalize_text(item.content)
            all_text = f"{title} {category} {content}"
            matched = len([term for term in q_terms if self._term_in_text(term, all_text)])
            title_hits = len([term for term in q_terms if self._term_in_text(term, title)])
            phrase = 0.20 if normalized_query and normalized_query in all_text else 0.0
            lexical_score = (matched / len(q_terms)) if q_terms else 0.0
            title_score = (title_hits / len(q_terms)) if q_terms else 0.0
            distance = getattr(item, "semantic_distance", None)
            try:
                semantic_score = max(0.0, min(1.0, 1.0 - float(distance))) if distance is not None else 0.0
            except (TypeError, ValueError):
                semantic_score = 0.0
            combined = 0.50 * lexical_score + 0.20 * title_score + phrase + 0.30 * semantic_score
            return (combined, semantic_score, -(item.id or 0))

        candidates.sort(key=score, reverse=True)
        return candidates[:limit]

    def _keyword_search(self, organization_id: int, agent_id: int | None, keywords: list[str], limit: int) -> list[KnowledgeBase]:
        if not keywords:
            return []
        conditions = []
        for keyword in keywords:
            pattern = f"%{keyword}%"
            conditions.extend((func.lower(KnowledgeBase.title).like(pattern), func.lower(KnowledgeBase.content).like(pattern), func.lower(KnowledgeBase.category).like(pattern)))
        statement = select(KnowledgeBase).where(
            KnowledgeBase.organization_id == organization_id,
            KnowledgeBase.is_active.is_(True),
            or_(*conditions),
        )
        if agent_id is not None:
            statement = statement.where(or_(KnowledgeBase.agent_id.is_(None), KnowledgeBase.agent_id == agent_id))
        statement = statement.order_by(KnowledgeBase.id.desc()).limit(limit)
        try:
            return list(self.db.scalars(statement).all())
        except Exception as exc:
            print("Keyword knowledge search error:", exc)
            return []

    def _semantic_search(self, organization_id: int, agent_id: int | None, query: str, limit: int) -> list[KnowledgeBase]:
        try:
            query_embedding = self.embedding_service.generate(query)
        except Exception as exc:
            print("Embedding generation error:", exc)
            return []
        distance = KnowledgeBase.embedding.cosine_distance(query_embedding)
        statement = select(KnowledgeBase, distance.label("similarity_distance")).where(
            KnowledgeBase.organization_id == organization_id,
            KnowledgeBase.is_active.is_(True),
            KnowledgeBase.embedding.is_not(None),
        )
        if agent_id is not None:
            statement = statement.where(or_(KnowledgeBase.agent_id.is_(None), KnowledgeBase.agent_id == agent_id))
        statement = statement.order_by(distance.asc()).limit(limit)
        try:
            rows = self.db.execute(statement).all()
        except Exception as exc:
            print("Semantic knowledge search error:", exc)
            return []
        relevant: list[KnowledgeBase] = []
        for knowledge, raw_distance in rows:
            try:
                item_distance = float(raw_distance)
            except (TypeError, ValueError):
                continue
            if item_distance <= self.MAX_COSINE_DISTANCE:
                setattr(knowledge, "semantic_distance", item_distance)
                relevant.append(knowledge)
        return relevant

    @classmethod
    def _extract_keywords(cls, query: str) -> list[str]:
        words = re.findall(r"[a-zA-Z0-9+#.-]+", (query or "").lower())
        result: list[str] = []
        for word in words:
            word = word.strip(".-")
            if len(word) < 2 or word in cls.STOP_WORDS or word in result:
                continue
            result.append(word)
        return result[: cls.MAX_KEYWORDS]

    @staticmethod
    def _term_in_text(term: str, text: str) -> bool:
        return bool(re.search(rf"(?<![a-zA-Z0-9+#]){re.escape(term.lower())}(?![a-zA-Z0-9+#])", text.lower()))

    @staticmethod
    def _normalize_text(text: str) -> str:
        return " ".join(str(text or "").lower().split())
