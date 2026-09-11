from __future__ import annotations

from app.services.conversation_query_service import ConversationQueryService
from app.services.semantic_conversation_service import SemanticConversationService


class ChatFlowEngine:
    """Orchestrates semantic analysis, strict scoped retrieval, grounding and synthesis."""

    MAX_QUESTIONS = 8
    RETRIEVAL_LIMIT = 4
    MAX_GROUNDED_ITEMS = 12
    KNOWLEDGE_INTENTS = {
        "company_courses", "topics", "fee", "discount", "duration", "timings",
        "duration_and_timings", "mode", "admission", "contact", "company_information",
        "details", "availability", "certificate", "payment", "eligibility",
    }

    def __init__(self, llm, retrieval_service, grounding_service, answer_orchestrator, knowledge_service):
        self.semantic = SemanticConversationService(llm)
        self.queries = ConversationQueryService()
        self.retrieval = retrieval_service
        self.grounding = grounding_service
        self.answer = answer_orchestrator
        self.knowledge_service = knowledge_service

    async def run(self, *, message, conversation_context, organization_id, agent_id, previous_subject=None):
        available_items = self._available_items(organization_id, agent_id)
        available_subjects = list(dict.fromkeys(
            str(getattr(item, "title", "") or "").strip()
            for item in available_items
            if str(getattr(item, "title", "") or "").strip()
        ))

        semantic = await self.semantic.analyze(
            message=message,
            conversation_context=conversation_context,
            available_subjects=available_subjects,
        )
        if semantic is None:
            semantic = self.semantic.fallback(
                message,
                conversation_context,
                available_subjects=available_subjects,
            )

        # A receptionist with no active assigned/shared knowledge must never
        # answer company-specific factual questions from another scope.
        if semantic.requires_knowledge and not available_items:
            return semantic, [], []

        if previous_subject:
            questions = [
                {**question, "subject": question.get("subject") or previous_subject}
                for question in semantic.questions
            ]
            semantic = semantic.__class__(
                intent=semantic.intent,
                subject=semantic.subject or previous_subject,
                questions=questions,
                response_style=semantic.response_style,
                requires_knowledge=semantic.requires_knowledge,
                wants_lead_action=semantic.wants_lead_action,
            )

        queries = self.queries.build_queries(
            semantic=semantic,
            fallback_subject=previous_subject,
            original_message=message,
        )[: self.MAX_QUESTIONS]

        if not semantic.requires_knowledge:
            return semantic, queries, []

        knowledge = []
        for query_plan in queries:
            results = self.retrieval.retrieve(
                organization_id=organization_id,
                query=query_plan["query"],
                limit=self.RETRIEVAL_LIMIT,
                subject=query_plan.get("subject"),
                agent_id=agent_id,
            )
            accepted_for_query = []
            for result in results:
                decision = self.grounding.evaluate(
                    query=query_plan["query"],
                    title=str(getattr(result, "title", "") or ""),
                    content=str(getattr(result, "content", "") or ""),
                    semantic_distance=getattr(result, "semantic_distance", None),
                )
                if decision.accepted:
                    accepted_for_query.append(result)

            # Retrieval relevance is a ranking signal, not permission to discard
            # the only knowledge document assigned to a receptionist. Natural
            # questions such as "what are the fees?" or "can I join online?"
            # often contain intent words that do not literally occur in the
            # source document. Ollama must see the scoped source and decide from
            # its actual content rather than receiving an artificial "no data".
            if not accepted_for_query and query_plan.get("intent") in self.KNOWLEDGE_INTENTS:
                accepted_for_query = self._scoped_fallback(
                    available_items,
                    subject=query_plan.get("subject"),
                    limit=self.RETRIEVAL_LIMIT,
                )

            knowledge.extend(accepted_for_query)

        deduped = []
        seen = set()
        for item in knowledge:
            key = getattr(item, "id", None)
            if key is None:
                key = (getattr(item, "title", ""), getattr(item, "content", ""))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
            if len(deduped) >= self.MAX_GROUNDED_ITEMS:
                break
        return semantic, queries, deduped

    @staticmethod
    def _scoped_fallback(items, subject: str | None, limit: int):
        candidates = list(items or [])
        if subject:
            from app.services.conversation_guard import ConversationGuard
            matched = [item for item in candidates if ConversationGuard.matches_subject(subject, item)]
            if matched:
                candidates = matched
        return candidates[:limit]

    def _available_items(self, organization_id, agent_id):
        if agent_id is None:
            return []
        try:
            items = self.knowledge_service.get_all(
                organization_id=organization_id,
                agent_id=agent_id,
                scope="available",
            )
            return [item for item in items if getattr(item, "is_active", True)]
        except Exception:
            return []
