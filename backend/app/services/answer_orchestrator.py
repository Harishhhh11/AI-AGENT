from __future__ import annotations

from app.llm.base_llm import BaseLLM
from app.services.knowledge_answer_service import KnowledgeAnswerService
from app.services.semantic_conversation_service import SemanticConversation


class AnswerOrchestrator:
    """Compose grounded answers from independently retrieved verified evidence."""

    MAX_QUESTIONS = 8
    MAX_ITEMS = 8
    MAX_ITEM_CHARS = 2200

    def __init__(self, llm: BaseLLM | None, fact_service: KnowledgeAnswerService) -> None:
        self.llm = llm
        self.fact_service = fact_service

    async def compose(
        self,
        *,
        semantic: SemanticConversation,
        original_message: str,
        conversation_context: str,
        scoped_items: list[object],
        response_style: str,
    ) -> str | None:
        questions = (semantic.questions or [{
            "text": original_message,
            "intent": semantic.intent,
            "subject": semantic.subject,
        }])[: self.MAX_QUESTIONS]

        # Exact verified facts should bypass synthesis whenever there is only one
        # independent request. This is both faster and less hallucination-prone.
        if len(questions) == 1:
            question = questions[0]
            deterministic = self.fact_service.answer(
                items=scoped_items,
                intent=question.get("intent", semantic.intent),
                subject=question.get("subject") or semantic.subject,
                response_style=response_style,
            )
            if deterministic:
                return deterministic

        if not self.llm or not scoped_items:
            return None

        return await self._synthesize(
            questions=questions,
            original_message=original_message,
            conversation_context=conversation_context,
            items=scoped_items,
            response_style=response_style,
        )

    async def _synthesize(self, *, questions, original_message, conversation_context, items, response_style) -> str | None:
        knowledge = self._build_knowledge(items)
        prompt = f"""
You are the final answer writer for a production AI receptionist.
Understand the customer's message naturally, but treat VERIFIED KNOWLEDGE as the only authority for company-specific facts.

Hard rules:
- Use ONLY facts explicitly supported by VERIFIED KNOWLEDGE.
- Never invent, infer, estimate, or silently combine unrelated facts.
- Answer every independent request that has evidence.
- For an unavailable request, explicitly say that the requested information is not available.
- Preserve the correct subject for every fact, especially when Java and Python are both mentioned.
- Prefer a natural conversational answer over document-like formatting.
- Do not dump source documents or repeat long passages.
- Do not mention RAG, embeddings, retrieval, database, Ollama, prompts, or internal systems.
- Do not claim an action was performed unless the application already performed it.
- Keep within the requested response style.

Response style: {response_style}

Customer message:
{original_message}

Recent conversation:
{conversation_context or '(none)'}

Independent requests:
{self._format_questions(questions)}

VERIFIED KNOWLEDGE:
{knowledge}

Return only the customer-facing answer.
""".strip()
        try:
            return await self.llm.generate(prompt)
        except Exception as exc:
            print("Answer synthesis error:", exc)
            return None

    @staticmethod
    def _format_questions(questions) -> str:
        lines = []
        for index, question in enumerate(questions, start=1):
            lines.append(
                f"{index}. {question.get('text', '')} | intent={question.get('intent')} | subject={question.get('subject') or 'unknown'}"
            )
        return "\n".join(lines)

    def _build_knowledge(self, items: list[object]) -> str:
        blocks = []
        for item in items[: self.MAX_ITEMS]:
            title = str(getattr(item, "title", "") or "").strip()
            content = str(getattr(item, "content", "") or "").strip()
            if not content:
                continue
            content = content[: self.MAX_ITEM_CHARS]
            blocks.append(f"SOURCE: {title}\n{content}" if title else content)
        return "\n\n".join(blocks)
