"""
Knowledge retrieval orchestration.

Responsible for retrieving relevant company knowledge
for the current conversation.

This service is completely company-agnostic.

Important:

Vector similarity alone is NOT enough.

When a subject is known, retrieved knowledge must also
be relevant to that subject. This prevents knowledge from
another course/product/service from leaking into the answer.

Examples:

    Current subject: Python
    Query: "How much?"
        -> Python knowledge allowed.

    Current subject: Java
    Query: "How much?"
        -> Java knowledge allowed only if Java knowledge exists.

    Current subject: Web Technology
    Query: "How much?"
        -> Python/Java knowledge must NOT be returned.
"""


import re


from app.services.knowledge_service import (
    KnowledgeService,
)


class RetrievalService:
    """
    General-purpose company knowledge retrieval service.
    """

    DEFAULT_LIMIT = 5

    MAX_LIMIT = 10

    # Minimum number of meaningful subject terms that should
    # appear in retrieved knowledge when a subject is explicit.
    #
    # For a one-word subject:
    #
    #     python
    #
    # one match is enough.
    #
    # For:
    #
    #     web development
    #
    # either the phrase or meaningful terms should match.
    MIN_SUBJECT_MATCHES = 1

    def __init__(
        self,
        knowledge_service: KnowledgeService,
    ) -> None:

        self.knowledge_service = (
            knowledge_service
        )

    # =========================================================
    # RETRIEVE
    # =========================================================

    def retrieve(
        self,
        organization_id: int,
        query: str,
        limit: int = DEFAULT_LIMIT,
        subject: str | None = None,
        agent_id: int | None = None,
    ):
        """
        Retrieve relevant company knowledge.

        Steps:

            1. Normalize query.
            2. Add current subject to semantic query.
            3. Search only inside the organization.
            4. Apply a subject relevance gate.
            5. Return only knowledge belonging to the
               current conversational subject.

        This prevents cross-topic leakage.
        """

        query = (
            query or ""
        ).strip()

        if not query:

            return []

        limit = max(
            1,
            min(
                limit,
                self.MAX_LIMIT,
            ),
        )

        normalized_subject = (
            self._normalize_subject(
                subject
            )
        )

        # -----------------------------------------------------
        # Build semantic query.
        # -----------------------------------------------------

        search_query = query

        if normalized_subject:

            search_query = (
                f"SUBJECT: "
                f"{normalized_subject}\n"
                f"QUERY: "
                f"{query}"
            )

        # -----------------------------------------------------
        # Search knowledge base.
        # -----------------------------------------------------

        try:

            results = (
                self.knowledge_service.search(
                    organization_id=organization_id,
                    query=search_query,
                    limit=limit,
                    agent_id=agent_id,
                )
            )

        except Exception as exc:

            print(
                "Knowledge retrieval error:",
                exc,
            )

            return []

        if not results:

            return []

        # -----------------------------------------------------
        # IMPORTANT:
        #
        # If there is no explicit subject, we can return the
        # semantic results normally.
        #
        # Example:
        #
        # "What courses do you offer?"
        #
        # There is no individual course subject.
        # -----------------------------------------------------

        if not normalized_subject:

            return results

        # -----------------------------------------------------
        # Subject relevance gate.
        #
        # This is the critical protection against:
        #
        # Python -> Java
        # Python -> Web Development
        # Java -> Python
        # Web -> Python
        #
        # leakage.
        # -----------------------------------------------------

        filtered_results = (
            self._filter_by_subject(
                results=results,
                subject=normalized_subject,
            )
        )

        # -----------------------------------------------------
        # If nothing matches the explicit subject, return
        # NOTHING.
        #
        # This is intentional.
        #
        # It is much safer for the AI to say:
        #
        # "I don't currently have verified information..."
        #
        # than to answer using another course's information.
        # -----------------------------------------------------

        return filtered_results

    # =========================================================
    # SUBJECT FILTER
    # =========================================================

    def _filter_by_subject(
        self,
        results,
        subject: str,
    ):
        """
        Keep only knowledge records that appear relevant to
        the requested subject.

        We inspect:

            - title
            - category
            - content

        We do NOT depend on company-specific names.

        The actual company/course names come from the
        knowledge base itself.
        """

        subject = (
            self._normalize_subject(
                subject
            )
        )

        if not subject:

            return list(
                results
            )

        subject_terms = (
            self._subject_terms(
                subject
            )
        )

        if not subject_terms:

            return []

        filtered = []

        for item in results:

            searchable_text = (
                self._build_searchable_text(
                    item
                )
            )

            normalized_text = (
                self._normalize_text(
                    searchable_text
                )
            )

            # -------------------------------------------------
            # Exact phrase match.
            #
            # Example:
            #
            # subject = "web development"
            #
            # content contains:
            #
            # "Web Development Course"
            #
            # This is the strongest match.
            # -------------------------------------------------

            if subject in normalized_text:

                filtered.append(
                    item
                )

                continue

            # -------------------------------------------------
            # Term-level matching.
            #
            # Useful for:
            #
            # "web development"
            #
            # when the database contains:
            #
            # "Web Development"
            #
            # in separate fields.
            # -------------------------------------------------

            matches = sum(
                1
                for term in subject_terms
                if self._term_matches(
                    term,
                    normalized_text,
                )
            )

            if matches >= self.MIN_SUBJECT_MATCHES:

                # For multi-word subjects, require enough
                # evidence to avoid weak matches.
                if len(subject_terms) >= 2:

                    # If two or more meaningful terms exist,
                    # require at least half of them.
                    required = max(
                        1,
                        (
                            len(subject_terms)
                            + 1
                        )
                        // 2,
                    )

                    if matches < required:

                        continue

                filtered.append(
                    item
                )

        return filtered

    # =========================================================
    # BUILD SEARCHABLE TEXT
    # =========================================================

    @staticmethod
    def _build_searchable_text(
        item,
    ) -> str:
        """
        Combine knowledge fields into one searchable string.

        Works with the current KnowledgeBase model:

            title
            category
            content
        """

        title = getattr(
            item,
            "title",
            "",
        )

        category = getattr(
            item,
            "category",
            "",
        )

        content = getattr(
            item,
            "content",
            "",
        )

        return " ".join(
            (
                str(
                    title or ""
                ),
                str(
                    category or ""
                ),
                str(
                    content or ""
                ),
            )
        )

    # =========================================================
    # SUBJECT TERMS
    # =========================================================

    @classmethod
    def _subject_terms(
        cls,
        subject: str,
    ) -> list[str]:
        """
        Convert a subject into meaningful searchable terms.

        Example:

            "web development"
                -> ["web", "development"]

            "python"
                -> ["python"]

            "c language"
                -> ["c", "language"]

        Generic conversational words are removed.
        """

        normalized = (
            cls._normalize_subject(
                subject
            )
        )

        if not normalized:

            return []

        words = re.findall(
            r"[a-zA-Z0-9+#.-]+",
            normalized,
        )

        ignored = {
            "the",
            "a",
            "an",

            "course",
            "courses",
            "training",
            "class",
            "classes",
            "program",
            "programs",

            "service",
            "services",

            "technology",
            "technologies",

            "language",

            "coursework",
            "details",
            "detail",
            "information",
            "info",
        }

        terms = []

        for word in words:

            word = (
                word.strip(
                    ".-"
                )
            )

            if not word:

                continue

            # C is meaningful even though it is one character.
            if (
                len(word) <= 1
                and word != "c"
            ):

                continue

            if word in ignored:

                continue

            if word not in terms:

                terms.append(
                    word
                )

        # If everything was removed but the subject itself is
        # meaningful, preserve it.
        if not terms:

            if normalized:

                return [
                    normalized
                ]

        return terms

    # =========================================================
    # TERM MATCH
    # =========================================================

    @staticmethod
    def _term_matches(
        term: str,
        text: str,
    ) -> bool:
        """
        Match a subject term safely.

        Word-boundary matching prevents:

            java

        from matching:

            javascript

        simply because "java" is a substring.
        """

        term = (
            term or ""
        ).strip().lower()

        text = (
            text or ""
        ).lower()

        if not term or not text:

            return False

        # -----------------------------------------------------
        # Special handling for C.
        #
        # "C programming" can be represented as:
        #
        # C
        #
        # and word-boundary matching is appropriate.
        # -----------------------------------------------------

        escaped = re.escape(
            term
        )

        return bool(
            re.search(
                rf"(?<![a-zA-Z0-9+#])"
                rf"{escaped}"
                rf"(?![a-zA-Z0-9+#])",
                text,
            )
        )

    # =========================================================
    # NORMALIZE SUBJECT
    # =========================================================

    @staticmethod
    def _normalize_subject(
        subject: str | None,
    ) -> str:

        if not subject:

            return ""

        return " ".join(
            str(
                subject
            )
            .strip()
            .lower()
            .split()
        )

    # =========================================================
    # NORMALIZE TEXT
    # =========================================================

    @staticmethod
    def _normalize_text(
        text: str,
    ) -> str:

        return " ".join(
            str(
                text or ""
            )
            .lower()
            .split()
        )
