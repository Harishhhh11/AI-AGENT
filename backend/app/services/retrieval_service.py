"""Knowledge retrieval orchestration with subject-aware tenant-safe ranking."""

from __future__ import annotations

import re

from app.services.conversation_guard import ConversationGuard
from app.services.knowledge_ranker import KnowledgeRanker
from app.services.knowledge_service import KnowledgeService


class RetrievalService:
    DEFAULT_LIMIT = 5
    MAX_LIMIT = 10
    CANDIDATE_LIMIT = 25

    def __init__(self, knowledge_service: KnowledgeService) -> None:
        self.knowledge_service = knowledge_service
        self.ranker = KnowledgeRanker()

    def retrieve(self, organization_id: int, query: str, limit: int = DEFAULT_LIMIT, subject: str | None = None, agent_id: int | None = None):
        query = (query or "").strip()
        if not query:
            return []
        try:
            limit = max(1, min(int(limit), self.MAX_LIMIT))
        except (TypeError, ValueError):
            limit = self.DEFAULT_LIMIT

        normalized_subject = self._normalize_subject(subject)
        retrieval_query = self._build_query(query, normalized_subject)
        try:
            if self._uses_sqlite():
                results = self._sqlite_scoped_search(
                    organization_id=organization_id,
                    agent_id=agent_id,
                    query=retrieval_query,
                    limit=self.CANDIDATE_LIMIT,
                )
            else:
                results = self.knowledge_service.search(
                    organization_id=organization_id,
                    query=retrieval_query,
                    limit=self.CANDIDATE_LIMIT,
                    agent_id=agent_id,
                )
        except Exception as exc:
            print("Knowledge retrieval error:", exc)
            results = []

        if normalized_subject:
            results = self._filter_by_subject(results, normalized_subject)

        # Search can miss a valid user-uploaded record when the query is mostly
        # intent vocabulary or when the local semantic backend is unavailable.
        # Fall back to the exact scoped knowledge set before declaring that the
        # receptionist has no answer.
        if not results:
            try:
                scoped = self.knowledge_service.get_all(
                    organization_id=organization_id,
                    agent_id=agent_id,
                    scope="available",
                )
            except Exception as exc:
                print("Scoped knowledge retrieval error:", exc)
                scoped = []
            if normalized_subject:
                scoped = self._filter_by_subject(scoped, normalized_subject)
            results = list(scoped or [])

        return self.ranker.rank(query=retrieval_query, items=list(results or []), limit=limit)

    def _uses_sqlite(self) -> bool:
        """SQLite cannot execute pgvector's PostgreSQL cosine-distance operator."""
        try:
            bind = self.knowledge_service.db.get_bind()
            return str(getattr(getattr(bind, "dialect", None), "name", "")).lower() == "sqlite"
        except Exception:
            return False

    def _sqlite_scoped_search(self, *, organization_id: int, agent_id: int | None, query: str, limit: int):
        """Use the tenant/agent scoped rows directly when local DB is SQLite."""
        scoped = self.knowledge_service.get_all(
            organization_id=organization_id,
            agent_id=agent_id,
            scope="available",
        )
        active = [item for item in scoped if getattr(item, "is_active", True)]
        terms = [
            token
            for token in re.findall(r"[a-zA-Z0-9+#.-]+", (query or "").lower())
            if len(token) > 1 and token not in {
                "what", "whats", "is", "are", "the", "a", "an", "for", "of", "to", "do", "you", "can",
                "i", "my", "your", "how", "much", "many", "please", "tell", "me", "about", "course", "courses",
                "online", "offline", "mode", "join", "get", "give", "have", "has", "and", "or",
            }
        ]
        if not terms:
            return active[:limit]

        def score(item):
            corpus = " ".join(
                str(getattr(item, attr, "") or "").lower()
                for attr in ("title", "category", "content")
            )
            title = str(getattr(item, "title", "") or "").lower()
            hits = sum(1 for term in terms if re.search(rf"(?<![a-z0-9+#]){re.escape(term)}(?![a-z0-9+#])", corpus))
            title_hits = sum(1 for term in terms if re.search(rf"(?<![a-z0-9+#]){re.escape(term)}(?![a-z0-9+#])", title))
            return (hits, title_hits, -(getattr(item, "id", 0) or 0))

        return sorted(active, key=score, reverse=True)[:limit]

    @staticmethod
    def _build_query(query: str, subject: str) -> str:
        normalized_query = (query or "").lower()
        return query if not subject or subject in normalized_query else f"{subject} {query}"

    def _filter_by_subject(self, results, subject: str):
        return [item for item in (results or []) if ConversationGuard.matches_subject(subject, item)]

    @staticmethod
    def _normalize_subject(subject: str | None) -> str:
        return " ".join(str(subject or "").strip().lower().split())
