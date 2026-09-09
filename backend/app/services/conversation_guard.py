"""Deterministic guards for conversational subject continuity and safety."""

from __future__ import annotations

import re


class ConversationGuard:
    """Validate retrieved knowledge against the active conversational subject."""

    GENERIC_TERMS = {
        "course", "courses", "class", "classes", "training", "program", "programs",
        "service", "services", "product", "products", "details", "information", "info",
        "technology", "technologies", "language", "the", "a", "an",
    }

    @classmethod
    def subject_terms(cls, subject: str | None) -> list[str]:
        if not subject:
            return []
        result: list[str] = []
        for token in re.findall(r"[a-z0-9+#.-]+", subject.lower()):
            token = token.strip(".-")
            if len(token) <= 1 or token in cls.GENERIC_TERMS or token in result:
                continue
            result.append(token)
        return result

    @classmethod
    def matches_subject(cls, subject: str | None, item: object) -> bool:
        terms = cls.subject_terms(subject)
        if not terms:
            return True
        corpus = " ".join(
            str(getattr(item, attr, "") or "").lower()
            for attr in ("title", "category", "content")
        )
        hits = sum(
            1
            for term in terms
            if re.search(rf"(?<![a-z0-9+#]){re.escape(term)}(?![a-z0-9+#])", corpus)
        )
        # A multi-word subject is a conjunction: all meaningful words are
        # required in the candidate instead of allowing a broad partial match.
        return hits == len(terms)
