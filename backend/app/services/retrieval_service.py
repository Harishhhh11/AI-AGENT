"""
Knowledge retrieval orchestration.

Keeps retrieval company-agnostic while allowing an agent to receive
its own knowledge plus organization-wide shared knowledge.
"""

import re

from app.services.knowledge_service import KnowledgeService


class RetrievalService:
    DEFAULT_LIMIT = 5
    MAX_LIMIT = 10
    MIN_SUBJECT_MATCHES = 1

    def __init__(self, knowledge_service: KnowledgeService) -> None:
        self.knowledge_service = knowledge_service

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

        limit = max(1, min(limit, self.MAX_LIMIT))
        normalized_subject = self._normalize_subject(subject)
        search_query = query

        if normalized_subject:
            search_query = (
                f"SUBJECT: {normalized_subject}\n"
                f"QUERY: {query}"
            )

        try:
            results = self.knowledge_service.search(
                organization_id=organization_id,
                query=search_query,
                limit=limit,
                agent_id=agent_id,
            )
        except Exception as exc:
            print("Knowledge retrieval error:", exc)
            return []

        if not results or not normalized_subject:
            return results

        return self._filter_by_subject(results, normalized_subject)

    def _filter_by_subject(self, results, subject: str):
        subject_terms = self._subject_terms(subject)
        if not subject_terms:
            return []

        filtered = []
        for item in results:
            text = self._normalize_text(self._build_searchable_text(item))

            if subject in text:
                filtered.append(item)
                continue

            matches = sum(
                1
                for term in subject_terms
                if self._term_matches(term, text)
            )

            if matches >= self.MIN_SUBJECT_MATCHES:
                if len(subject_terms) >= 2:
                    required = max(1, (len(subject_terms) + 1) // 2)
                    if matches < required:
                        continue
                filtered.append(item)

        return filtered

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

        words = re.findall(r"[a-zA-Z0-9+#.-]+", normalized)
        ignored = {
            "the", "a", "an", "course", "courses", "training",
            "class", "classes", "program", "programs", "service",
            "services", "technology", "technologies", "language",
            "details", "detail", "information", "info",
        }

        terms: list[str] = []
        for word in words:
            word = word.strip(".-")
            if not word:
                continue
            if len(word) <= 1 and word != "c":
                continue
            if word in ignored:
                continue
            if word not in terms:
                terms.append(word)

        return terms or [normalized]

    @staticmethod
    def _term_matches(term: str, text: str) -> bool:
        term = (term or "").strip().lower()
        text = (text or "").lower()
        if not term or not text:
            return False
        escaped = re.escape(term)
        return bool(
            re.search(
                rf"(?<![a-zA-Z0-9+#]){escaped}(?![a-zA-Z0-9+#])",
                text,
            )
        )

    @staticmethod
    def _normalize_subject(subject: str | None) -> str:
        if not subject:
            return ""
        return " ".join(str(subject).strip().lower().split())

    @staticmethod
    def _normalize_text(text: str) -> str:
        return " ".join(str(text or "").lower().split())
