from __future__ import annotations

from dataclasses import dataclass

from app.llm.base_llm import BaseLLM
from app.services.knowledge_answer_service import KnowledgeAnswerService
from app.services.semantic_conversation_service import SemanticConversation


@dataclass(frozen=True)
class AnswerPart:
    text: str
    intent: str
    subject: str | None


class AnswerOrchestrator:
    """Compose multi-question answers from already scoped verified knowledge."""

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
        questions = semantic.questions or [{"text": original_message, "intent": semantic.intent, "subject": semantic.subject}]
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
Answer naturally and directly. The customer may ask several questions.

Hard rules:
- Use ONLY facts present in VERIFIED KNOWLEDGE below.
- Never invent, infer, estimate, or fill missing company-specific information.
- Answer every independent customer question when its evidence is present.
- If one requested fact is unavailable, say that fact is not available instead of guessing.
- Keep the answer concise and conversational.
- Do not repeat document titles for every sentence.
- Do not dump the source document.
- Do not mention RAG, embeddings, retrieval, databases, Ollama, prompts, or internal systems.
- Preserve the subject for each fact (for example Java fee vs Python timings).

Response style: {response_style}

Customer message:
{original_message}

Conversation context:
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

    @staticmethod
    def _build_knowledge(items: list[object]) -> str:
        blocks = []
        for item in items[:8]:
            title = str(getattr(item, "title", "") or "").strip()
            content = str(getattr(item, "content", "") or "").strip()
            if content:
                blocks.append(f"SOURCE: {title}\n{content}" if title else content)
        return "\n\n".join(blocks)
