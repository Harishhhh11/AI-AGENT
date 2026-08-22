"""
AI Receptionist chat service.

Main orchestration layer.

Responsibilities:

- Conversation creation
- Conversation memory
- Context understanding
- Subject resolution
- Intent resolution
- Knowledge retrieval
- Knowledge grounding
- Response-length control
- AI response generation
- Message persistence
- Lead conversation handling
- Lead creation/update

This service is completely company-agnostic.

It does NOT contain company-specific subjects such as:

- Python
- Java
- C
- Web Development
- AI/ML
- Any particular product or service

All company-specific information must come from the
organization's knowledge base.
"""

import re

from sqlalchemy.orm import Session

from app.llm.llm_factory import get_llm

from app.prompts.receptionist import (
    RECEPTIONIST_SYSTEM_PROMPT,
)

from app.services.conversation_service import (
    ConversationService,
)

from app.services.knowledge_service import (
    KnowledgeService,
)

from app.services.context_service import (
    ContextService,
)

from app.services.retrieval_service import (
    RetrievalService,
)

from app.services.lead_extractor import (
    LeadExtractor,
)

from app.services.lead_service import (
    LeadService,
)

from app.services.lead_context_service import (
    LeadContextService,
)

from app.tools.base import ToolContext

from app.tools.registry import ToolOrchestrator

class ChatService:
    """Main AI receptionist orchestration service."""

    CONVERSATION_HISTORY_LIMIT = 8
    KNOWLEDGE_LIMIT = 5
    MAX_KNOWLEDGE_CHARS = 4500
    MAX_CONVERSATION_CONTEXT_CHARS = 4500
    MAX_SHORT_RESPONSE_CHARS = 350
    MAX_MEDIUM_RESPONSE_CHARS = 900
    MAX_LONG_RESPONSE_CHARS = 1800

    def __init__(self, db: Session) -> None:
        self.db = db
        self.llm = get_llm()
        self.conversation_service = ConversationService(db)
        self.knowledge_service = KnowledgeService(db)
        self.retrieval_service = RetrievalService(self.knowledge_service)
        self.context_service = ContextService(message_limit=self.CONVERSATION_HISTORY_LIMIT)
        self.lead_extractor = LeadExtractor()
        self.lead_service = LeadService(db)
        self.lead_context_service = LeadContextService()
        self.tool_orchestrator = ToolOrchestrator()

    async def generate_response(
        self,
        message: str,
        organization_id: int,
        user_id: int | None = None,
        session_id: str | None = None,
        agent_id: int | None = None,
        agent_instructions: str | None = None,
    ) -> tuple[str, str]:
        message = (message or "").strip()
        if not message:
            return session_id or "", "How can I help you?"

        conversation = self.conversation_service.get_or_create_conversation(
            session_id=session_id,
            organization_id=organization_id,
            user_id=user_id,
            agent_id=agent_id,
        )
        self.conversation_service.add_message(conversation_id=conversation.id, role="user", content=message)
        all_messages = self.conversation_service.get_messages(conversation.id)
        recent_messages = list(all_messages)[-self.CONVERSATION_HISTORY_LIMIT:]
        previous_messages = self._remove_current_message(recent_messages, message)

        analysis = self.context_service.analyze_message(message=message, messages=previous_messages)
        message_type = analysis.get("message_type") or "general"
        current_subject = analysis.get("subject")
        explicit_subject = analysis.get("explicit_subject")
        previous_subject = analysis.get("previous_subject")
        intent = analysis.get("intent") or "general"
        response_style = analysis.get("response_style") or "short"
        requires_knowledge = bool(analysis.get("requires_knowledge", False))
        question_count = analysis.get("question_count", 1)
        retrieval_query = (analysis.get("retrieval_query") or "").strip()

        conversation_context = self._limit_text(
            self.context_service.build_context(previous_messages),
            self.MAX_CONVERSATION_CONTEXT_CHARS,
        )

        lead_messages = list(previous_messages)
        lead_messages.append({"role": "user", "content": message})
        persisted_lead = self.lead_service.get_lead_for_conversation(
            conversation_id=conversation.id,
            organization_id=organization_id,
        )
        lead_context = self.lead_context_service.build_context(
            conversation=lead_messages,
            extracted_lead=persisted_lead,
        )
        self._recover_lead_state_from_history(lead_context=lead_context, messages=lead_messages)

        await self.tool_orchestrator.decide_and_execute(
            llm=self.llm,
            context=ToolContext(
                db=self.db,
                organization_id=organization_id,
                conversation_id=conversation.id,
                user_id=user_id,
                message=message,
                lead_context=lead_context,
            ),
        )

        if lead_context.is_lead:
            active_lead_subject = current_subject or previous_subject
            if not lead_context.interest and active_lead_subject:
                lead_context.interest = active_lead_subject

        active_lead_field = self._get_active_lead_field(previous_messages)
        is_valid_active_lead_answer = False
        if active_lead_field:
            is_valid_active_lead_answer, _ = self.lead_context_service.validate_field_answer(active_lead_field, message)

        is_new_lead_intent = self.lead_context_service.detect_lead_intent(message)
        normalized_current_message = message.lower().strip()
        question_like = "?" in normalized_current_message or normalized_current_message.startswith(("what ", "which ", "how ", "do ", "does ", "is ", "are ", "can ", "could ", "when ", "where "))
        is_new_knowledge_question = bool(
            not is_new_lead_intent
            and (requires_knowledge or intent not in {"general", "lead"} or question_like)
        )
        if active_lead_field and (is_new_lead_intent or (is_new_knowledge_question and not is_valid_active_lead_answer)):
            active_lead_field = None

        if lead_context.is_lead and active_lead_field:
            lead_field_response = await self._handle_active_lead_field(
                message=message,
                lead_context=lead_context,
                active_field=active_lead_field,
                conversation_id=conversation.id,
                organization_id=organization_id,
            )
            if lead_field_response:
                response = self._apply_response_length_guard(
                    response=self._clean_response(lead_field_response),
                    response_style="short",
                )
                self.conversation_service.add_message(conversation_id=conversation.id, role="assistant", content=response)
                return conversation.session_id, response

        if self._is_active_lead_collection(lead_context) and not (is_new_knowledge_question and not is_valid_active_lead_answer):
            lead_question = self.lead_context_service.get_next_question(lead_context)
            if lead_question:
                response = self._apply_response_length_guard(self._clean_response(lead_question), "short")
                self.conversation_service.add_message(conversation_id=conversation.id, role="assistant", content=response)
                await self._save_lead_context(conversation_id=conversation.id, organization_id=organization_id, lead_context=lead_context)
                return conversation.session_id, response

        if lead_context.is_complete and message_type == "confirmation":
            response = "You're welcome! How else can I help you?"
            self.conversation_service.add_message(conversation_id=conversation.id, role="assistant", content=response)
            await self._save_lead_context(conversation_id=conversation.id, organization_id=organization_id, lead_context=lead_context)
            return conversation.session_id, response

        if message_type == "unclear":
            response = "Could you please clarify what you'd like to know?"
            self.conversation_service.add_message(conversation_id=conversation.id, role="assistant", content=response)
            return conversation.session_id, response

        knowledge_items = []
        if requires_knowledge:
            retrieval_subject = current_subject
            if not retrieval_subject and message_type in {"follow_up", "confirmation"}:
                retrieval_subject = previous_subject
            if not retrieval_query:
                retrieval_query = message
            knowledge_items = await self.retrieval_service.retrieve(
                query=retrieval_query,
                organization_id=organization_id,
                limit=self.KNOWLEDGE_LIMIT,
                subject=retrieval_subject,
            )

        knowledge_context = self._build_knowledge_context(knowledge_items)
        verified_state = "VERIFIED COMPANY KNOWLEDGE AVAILABLE." if knowledge_items else "NO VERIFIED COMPANY KNOWLEDGE WAS FOUND."
        lead_state = self._build_lead_state_text(lead_context)
        length_instruction = self._get_length_instruction(response_style)
        prompt = RECEPTIONIST_SYSTEM_PROMPT.format(
            company_name="the organization",
            customer_message=message,
            active_subject=current_subject or previous_subject or "",
            intent=intent,
            question_count=question_count,
            response_style=response_style,
            lead_state=lead_state,
            verified_state=verified_state,
            knowledge_context=knowledge_context,
            conversation_context=conversation_context,
            length_instruction=length_instruction,
        )
        if agent_instructions:
            prompt = f"{prompt}\n\nAGENT-SPECIFIC INSTRUCTIONS:\n{agent_instructions.strip()}"
        response = await self.llm.generate(prompt)
        response = self._clean_response(response)
        if not response:
            response = "Sorry, I couldn't generate a response right now."
        response = self._apply_response_length_guard(response=response, response_style=response_style)
        self.conversation_service.add_message(conversation_id=conversation.id, role="assistant", content=response)
        await self._save_lead_context(conversation_id=conversation.id, organization_id=organization_id, lead_context=lead_context)
        return conversation.session_id, response

    @staticmethod
    def _apply_response_length_guard(response: str, response_style: str) -> str:
        response = str(response or "").strip()
        if not response:
            return response
        style = (response_style or "short").strip().lower()
        maximum = 350 if style == "short" else 900 if style == "medium" else 1800
        if len(response) <= maximum:
            return response
        shortened = response[:maximum]
        sentence_end = max(shortened.rfind("."), shortened.rfind("?"), shortened.rfind("!"))
        if sentence_end >= int(maximum * 0.45):
            return shortened[: sentence_end + 1].strip()
        suffix = "..."
        return (response[: maximum - len(suffix)].rstrip() + suffix).strip()

