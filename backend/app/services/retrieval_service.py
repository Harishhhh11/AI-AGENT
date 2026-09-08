"""Knowledge retrieval orchestration.

Retrieves organization-scoped knowledge using both direct keyword search and
semantic search, preserves the active agent boundary, and ranks candidates
for answer generation.
"""

from __future__ import annotations

import re

from app.services.knowledge_ranker import KnowledgeRanker
from app.services.knowledge_service import KnowledgeService


class RetrievalService:
    DEFAULT_LIMIT = 5
    MAX_LIMIT = 10
    CANDIDATE_LIMIT = 12

    def __init__(self, knowledge_service: KnowledgeService) -> None:
        self.knowledge_service = knowledge_service
        self.ranker = KnowledgeRanker()

    def retrieve(
        self,
        organization_id: int,
        query: str,
        limit: int = DEFAULT_LIMIT,
        subject: str | None = None,
        agent_id: int | None = None,
    ):
        query = (query or "").strip()
        if not query:
            return []

        try:
            limit = max(1, min(int(limit or self.DEFAULT_LIMIT), self.MAX_LIMIT))
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
            return []

        if normalized_subject:
            results = self._filter_by_subject(results, normalized_subject)

        return self.ranker.rank(
            query=retrieval_query,
            items=list(results or []),
            limit=limit,
        )

    @staticmethod
    def _build_query(query: str, subject: str) -> str:
        if not subject or subject in query.lower():
            return query
        return f"{subject} {query}"

    def _filter_by_subject(self, results, subject: str):
        terms = self._subject_terms(subject)
        if not terms:
            return list(results or [])

        filtered = []
        for item in results or []:
            searchable = self._normalize_text(self._build_searchable_text(item))
            matched = sum(self._term_matches(term, searchable) for term in terms)
            if subject in searchable or matched >= self._required_matches(len(terms)):
                filtered.append(item)
        return filtered

    @staticmethod
    def _required_matches(term_count: int) -> int:
        if term_count <= 1:
            return 1
        return max(1, (term_count + 1) // 2)

    @staticmethod
    def _build_searchable_text(item) -> str:
        return " ".join(
            str(getattr(item, "title", "") or ""),
            str(getattr(item, "category", "") or ""),
            str(getattr(item, "content", "") or ""),
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
