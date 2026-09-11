from __future__ import annotations

from app.services.conversation_query_service import ConversationQueryService
from app.services.semantic_conversation_service import SemanticConversationService


class ChatFlowEngine:
    """Orchestrate semantic understanding, scoped retrieval, grounding and answer synthesis."""

    MAX_QUESTIONS = 8
    RETRIEVAL_LIMIT = 6
    MAX_GROUNDED_ITEMS = 16
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
        available_subjects = self._subjects(available_items)

        semantic = await self.semantic.analyze(
            message=message,
            conversation_context=conversation_context,
            available_subjects=available_subjects,
        )
        if semantic is None:
            semantic = self.semantic.fallback(message, conversation_context, available_subjects=available_subjects)

        if previous_subject:
            semantic = self._apply_previous_subject(semantic, previous_subject)

        if semantic.requires_knowledge and not available_items:
            return semantic, [], []

        queries = self.queries.build_queries(
            semantic=semantic,
            fallback_subject=previous_subject,
            original_message=message,
        )[: self.MAX_QUESTIONS]
        if not semantic.requires_knowledge:
            return semantic, queries, []

        knowledge = []
        for query_plan in queries:
            scoped_subject = query_plan.get("subject") or semantic.subject or previous_subject
            results = self.retrieval.retrieve(
                organization_id=organization_id,
                query=query_plan["query"],
                limit=self.RETRIEVAL_LIMIT,
                subject=scoped_subject,
                agent_id=agent_id,
            )
            accepted = self._ground(query_plan, results)
            if not accepted and query_plan.get("intent") in self.KNOWLEDGE_INTENTS:
                accepted = self._scoped_fallback(available_items, scoped_subject, self.RETRIEVAL_LIMIT)
            knowledge.extend(accepted)

        deduped = []
        seen = set()
        for item in knowledge:
            key = getattr(item, "id", None) or (getattr(item, "title", ""), getattr(item, "content", ""))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
            if len(deduped) >= self.MAX_GROUNDED_ITEMS:
                break
        return semantic, queries, deduped

    def _ground(self, query_plan, results):
        accepted = []
        for result in results or []:
            decision = self.grounding.evaluate(
                query=query_plan["query"],
                title=str(getattr(result, "title", "") or ""),
                content=str(getattr(result, "content", "") or ""),
                semantic_distance=getattr(result, "semantic_distance", None),
            )
            if decision.accepted:
                accepted.append(result)
        return accepted

    @staticmethod
    def _scoped_fallback(items, subject, limit):
        candidates = list(items or [])
        if subject:
            from app.services.conversation_guard import ConversationGuard
            matched = [item for item in candidates if ConversationGuard.matches_subject(subject, item)]
            if matched:
                candidates = matched
            else:
                # When the receptionist has exactly one scoped document, the document
                # itself is the authority. Do not throw it away because a query phrase
                # is semantically unrelated to its title.
                if len(candidates) > 1:
                    return []
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

    @staticmethod
    def _subjects(items):
        return list(dict.fromkeys(
            str(getattr(item, "title", "") or "").strip()
            for item in items
            if str(getattr(item, "title", "") or "").strip()
        ))

    @staticmethod
    def _apply_previous_subject(semantic, previous_subject):
        questions = [
            {**question, "subject": question.get("subject") or previous_subject}
            for question in semantic.questions
        ]
        return semantic.__class__(
            intent=semantic.intent,
            subject=semantic.subject or previous_subject,
            questions=questions,
            response_style=semantic.response_style,
            requires_knowledge=semantic.requires_knowledge,
            wants_lead_action=semantic.wants_lead_action,
        )
