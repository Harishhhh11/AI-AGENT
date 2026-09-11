from __future__ import annotations

from app.services.answer_orchestrator import AnswerOrchestrator
from app.services.conversation_query_service import ConversationQueryService
from app.services.semantic_conversation_service import SemanticConversationService


class ChatFlowEngine:
    """Orchestrates semantic analysis, query decomposition, retrieval and synthesis."""

    def __init__(self, llm, retrieval_service, grounding_service, answer_orchestrator, knowledge_service):
        self.semantic = SemanticConversationService(llm)
        self.queries = ConversationQueryService()
        self.retrieval = retrieval_service
        self.grounding = grounding_service
        self.answer = answer_orchestrator
        self.knowledge_service = knowledge_service

    async def run(self, *, message, conversation_context, organization_id, agent_id, previous_subject=None):
        available_subjects = self._subjects(organization_id, agent_id)
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

        if previous_subject and not semantic.subject:
            semantic = semantic.__class__(
                intent=semantic.intent,
                subject=previous_subject,
                questions=[
                    {
                        **q,
                        "subject": q.get("subject") or previous_subject,
                    }
                    for q in semantic.questions
                ],
                response_style=semantic.response_style,
                requires_knowledge=semantic.requires_knowledge,
                wants_lead_action=semantic.wants_lead_action,
            )

        queries = self.queries.build_queries(
            semantic=semantic,
            fallback_subject=previous_subject,
            original_message=message,
        )
        knowledge = []
        for item in queries[:8]:
            results = self.retrieval.retrieve(
                organization_id=organization_id,
                query=item["query"],
                limit=6,
                subject=item.get("subject"),
                agent_id=agent_id,
            )
            for result in results:
                decision = self.grounding.evaluate(
                    query=item["query"],
                    title=str(getattr(result, "title", "") or ""),
                    content=str(getattr(result, "content", "") or ""),
                    semantic_distance=getattr(result, "semantic_distance", None),
                )
                if decision.accepted or item.get("subject"):
                    knowledge.append(result)
        deduped = []
        seen = set()
        for item in knowledge:
            key = getattr(item, "id", id(item))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
            if len(deduped) >= 12:
                break
        return semantic, queries, deduped

    def _subjects(self, organization_id, agent_id):
        try:
            items = self.knowledge_service.get_all(
                organization_id=organization_id,
                agent_id=agent_id,
                scope="available",
            )
        except Exception:
            return []
        return [
            str(getattr(item, "title", "") or "").strip()
            for item in items
            if getattr(item, "is_active", True) and str(getattr(item, "title", "") or "").strip()
        ]
