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
        # intent vocabulary (for example "what topics are covered") or when the
        # local embedding backend is unavailable. Fall back to the exact scoped
        # knowledge set before declaring that the receptionist has no answer.
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

    @staticmethod
    def _build_query(query: str, subject: str) -> str:
        normalized_query = (query or "").lower()
        return query if not subject or subject in normalized_query else f"{subject} {query}"

    def _filter_by_subject(self, results, subject: str):
        return [item for item in (results or []) if ConversationGuard.matches_subject(subject, item)]

    @staticmethod
    def _build_searchable_text(item) -> str:
        return " ".join(
            (
                str(getattr(item, "title", "") or ""),
                str(getattr(item, "category", "") or ""),
                str(getattr(item, "content", "") or ""),
            )
        )

    @classmethod
    def _subject_terms(cls, subject: str) -> list[str]:
        normalized = cls._normalize_subject(subject)
        if not normalized:
            return []
        ignored = {
            "the", "a", "an", "course", "courses", "training", "class", "classes",
            "program", "programs", "service", "services", "technology", "technologies",
            "language", "details", "detail", "information", "info",
        }
        terms = []
        for word in re.findall(r"[a-zA-Z0-9+#.-]+", normalized):
            word = word.strip(".-")
            if not word or len(word) <= 1 or word in ignored or word in terms:
                continue
            terms.append(word)
        return terms or [normalized]

    @staticmethod
    def _term_matches(term: str, text: str) -> bool:
        if not term or not text:
            return False
        return bool(re.search(rf"(?<![a-zA-Z0-9+#]){re.escape(term.lower())}(?![a-zA-Z0-9+#])", text.lower()))

    @staticmethod
    def _normalize_subject(subject: str | None) -> str:
        return " ".join(str(subject or "").strip().lower().split())

    @staticmethod
    def _normalize_text(text: str) -> str:
        return " ".join(str(text or "").lower().split())
