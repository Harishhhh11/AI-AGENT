from __future__ import annotations

from app.services.answer_orchestrator import AnswerOrchestrator
from app.services.conversation_query_service import ConversationQueryService
from app.services.semantic_conversation_service import SemanticConversationService


class ChatFlowEngine:
    """Orchestrates semantic analysis, strict scoped retrieval, grounding and synthesis."""

    MAX_QUESTIONS = 8
    RETRIEVAL_LIMIT = 4
    MAX_GROUNDED_ITEMS = 12

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
            if getattr(item, "is_active", True) and str(getattr(item, "title", "") or "").strip()
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

        # A receptionist with no assigned/shared knowledge must never answer
        # company-specific factual questions from unrelated/default data.
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
            for result in results:
                decision = self.grounding.evaluate(
                    query=query_plan["query"],
                    title=str(getattr(result, "title", "") or ""),
                    content=str(getattr(result, "content", "") or ""),
                    semantic_distance=getattr(result, "semantic_distance", None),
                )
                if decision.accepted:
                    knowledge.append(result)

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

    def _available_items(self, organization_id, agent_id):
        if agent_id is None:
            return []
        try:
            return self.knowledge_service.get_all(
                organization_id=organization_id,
                agent_id=agent_id,
                scope="available",
            )
        except Exception:
            return []
