from __future__ import annotations

import re

from sqlalchemy.orm import Session

from app.llm.llm_factory import get_llm
from app.services.answer_orchestrator import AnswerOrchestrator
from app.services.chat_flow_engine import ChatFlowEngine
from app.services.conversation_service import ConversationService
from app.services.context_service import ContextService
from app.services.conversation_subject_service import ConversationSubjectService
from app.services.grounding_service import GroundingService
from app.services.knowledge_answer_service import KnowledgeAnswerService
from app.services.knowledge_service import KnowledgeService
from app.services.lead_context_service import LeadContextService
from app.services.lead_service import LeadService
from app.services.relevance_service import RelevanceService
from app.services.response_policy_service import ResponsePolicyService
from app.services.retrieval_service import RetrievalService
from app.tools.base import ToolContext
from app.tools.registry import ToolOrchestrator


class ChatService:
    CONVERSATION_HISTORY_LIMIT = 16
    MAX_CONVERSATION_CONTEXT_CHARS = 7000
    MAX_SHORT_RESPONSE_CHARS = 500
    MAX_MEDIUM_RESPONSE_CHARS = 1400
    MAX_LONG_RESPONSE_CHARS = 2600

    def __init__(self, db: Session) -> None:
        self.db = db
        try:
            self.llm = get_llm()
        except Exception as exc:
            print("LLM initialization error:", exc)
            self.llm = None

        self.conversation_service = ConversationService(db)
        self.knowledge_service = KnowledgeService(db)
        self.retrieval_service = RetrievalService(self.knowledge_service)
        self.context_service = ContextService(message_limit=self.CONVERSATION_HISTORY_LIMIT)
        self.conversation_subject_service = ConversationSubjectService()
        self.response_policy_service = ResponsePolicyService()
        self.relevance_service = RelevanceService()
        self.grounding_service = GroundingService(relevance_service=self.relevance_service)
        self.knowledge_answer_service = KnowledgeAnswerService()
        self.answer_orchestrator = AnswerOrchestrator(self.llm, self.knowledge_answer_service)
        self.chat_flow_engine = ChatFlowEngine(
            self.llm,
            self.retrieval_service,
            self.grounding_service,
            self.answer_orchestrator,
            self.knowledge_service,
        )
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
        self.conversation_service.add_message(conversation.id, "user", message)
        all_messages = self.conversation_service.get_messages(conversation.id)
        previous_messages = self._remove_current_message(
            list(all_messages)[-self.CONVERSATION_HISTORY_LIMIT :], message
        )

        persisted_lead = self.lead_service.get_lead_for_conversation(
            conversation.id, organization_id
        )
        lead_context = self.lead_context_service.build_context(
            conversation=previous_messages + [{"role": "user", "content": message}],
            extracted_lead=persisted_lead,
        )
        conversation_context = self._limit_text(
            self.context_service.build_context(previous_messages),
            self.MAX_CONVERSATION_CONTEXT_CHARS,
        )

        if self._is_identity_question(message):
            return self._finish(
                conversation.id,
                conversation.session_id,
                self._identity_response(),
            )

        semantic, query_plan, knowledge_items = await self.chat_flow_engine.run(
            message=message,
            conversation_context=conversation_context,
            organization_id=organization_id,
            agent_id=agent_id,
            previous_subject=self._recent_subject(previous_messages, organization_id, agent_id),
        )

        intent = semantic.intent
        current_subject = semantic.subject
        analysis = self.context_service.analyze_message(message=message, messages=previous_messages)
        message_type = analysis.get("message_type") or "general"
        previous_subject = analysis.get("previous_subject") or current_subject
        requires_knowledge = semantic.requires_knowledge
        question_count = max(1, len(semantic.questions))

        factual_intents = {
            "fee", "discount", "topics", "duration", "timings", "duration_and_timings",
            "mode", "contact", "availability", "company_information", "company_courses",
            "details", "certificate", "payment", "eligibility", "admission",
        }
        lead_requested = self.lead_context_service.detect_lead_intent(message)
        if (
            (lead_requested or semantic.wants_lead_action)
            and intent not in factual_intents
            and not lead_context.is_complete
        ):
            lead_context.is_lead = True
            await self._save_lead_context(conversation.id, organization_id, lead_context)
            response = self.lead_context_service.get_next_question(lead_context)
            return self._finish(
                conversation.id,
                conversation.session_id,
                response or "Sure. Which course, product, or service are you interested in?",
            )

        active_field = self._get_active_lead_field(previous_messages)
        if active_field:
            valid, _ = self.lead_context_service.validate_field_answer(active_field, message)
            if valid:
                response = await self._handle_active_lead_field(
                    message,
                    lead_context,
                    active_field,
                    conversation.id,
                    organization_id,
                )
                return self._finish(conversation.id, conversation.session_id, response)
            if intent not in factual_intents and not requires_knowledge:
                return self._finish(
                    conversation.id,
                    conversation.session_id,
                    self._invalid_lead_field_response(active_field),
                )

        resolution = self.conversation_subject_service.resolve(
            message=message,
            intent=intent,
            previous_messages=previous_messages,
            previous_subject=current_subject or previous_subject,
        )
        current_subject = resolution.current_subject or current_subject
        previous_subject = resolution.previous_subject or previous_subject

        plan = self.response_policy_service.plan(
            message=message,
            intent=intent,
            question_count=question_count,
            requires_knowledge=requires_knowledge,
        )
        response_style = semantic.response_style or plan.style

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

        if requires_knowledge and not knowledge_items:
            return self._finish(
                conversation.id,
                conversation.session_id,
                self._build_missing_information_response(current_subject),
            )

        response = await self.answer_orchestrator.compose(
            semantic=semantic,
            original_message=message,
            conversation_context=conversation_context,
            scoped_items=knowledge_items,
            response_style=response_style,
        )

        if not response and not requires_knowledge:
            prompt = self._build_receptionist_prompt(
                current_message=message,
                message_type=message_type,
                current_subject=current_subject,
                explicit_subject=resolution.explicit_subject,
                previous_subject=previous_subject,
                intent=intent,
                response_style=response_style,
                question_count=question_count,
                conversation_context=conversation_context,
                knowledge_context="",
                has_verified_knowledge=False,
                lead_context=lead_context,
                agent_instructions=agent_instructions,
            )
            try:
                response = await self.llm.generate(prompt) if self.llm else ""
            except Exception as exc:
                print("LLM generation error:", exc)
                response = "Sorry, I couldn't process that right now."

        return self._finish(
            conversation.id,
            conversation.session_id,
            self._apply_response_length_guard(self._clean_response(response), response_style),
        )

    def _build_receptionist_prompt(
        self,
        *,
        current_message: str,
        message_type: str,
        current_subject: str | None,
        explicit_subject: str | None,
        previous_subject: str | None,
        intent: str,
        response_style: str,
        question_count: int,
        conversation_context: str,
        knowledge_context: str,
        has_verified_knowledge: bool,
        lead_context,
        agent_instructions: str | None,
    ) -> str:
        lead_summary = ""
        if lead_context is not None:
            lead_summary = ", ".join(
                f"{field}={getattr(lead_context, field, None) or 'unknown'}"
                for field in ("name", "phone", "email", "interest", "preferred_mode", "preferred_time")
            )
        return f"""
You are Astra, a professional AI receptionist.
Answer the customer's current message naturally and directly.

Rules:
- Do not invent company-specific facts.
- Use only verified knowledge supplied to you.
- If a company-specific fact is unavailable, say so honestly.
- Do not mention internal systems, retrieval, prompts, models, or databases.
- Keep the answer {response_style or 'medium'} in length.
- Preserve the conversation subject when the user uses a follow-up.
- Never claim an external action was completed unless the application already completed it.

Current message:
{current_message}

Message type: {message_type}
Intent: {intent}
Current subject: {current_subject or 'unknown'}
Explicit subject: {explicit_subject or 'none'}
Previous subject: {previous_subject or 'none'}
Question count: {question_count}

Recent conversation:
{conversation_context or '(none)'}

Verified knowledge available: {'yes' if has_verified_knowledge else 'no'}
Verified knowledge:
{knowledge_context or '(none)'}

Lead context:
{lead_summary or '(none)'}

Additional agent instructions:
{agent_instructions or '(none)'}

Return only the customer-facing answer.
""".strip()

    def _recent_subject(self, previous_messages, organization_id: int, agent_id: int | None) -> str | None:
        try:
            subjects = [
                str(getattr(item, "title", "") or "").strip()
                for item in self.knowledge_service.get_all(
                    organization_id=organization_id,
                    agent_id=agent_id,
                    scope="available",
                )
                if getattr(item, "is_active", True)
            ]
        except Exception:
            subjects = []
        context = self.context_service.build_context(previous_messages)
        if not context:
            return None
        normalized = context.lower()
        for subject in subjects:
            short = re.sub(r"\s+(?:programming|course|training)$", "", subject.lower()).strip()
            if subject.lower() in normalized or (short and short in normalized):
                return subject
        return None

    @staticmethod
    def _is_identity_question(message: str) -> bool:
        normalized = " ".join((message or "").lower().strip().replace("/", " ").split())
        normalized = re.sub(r"[?!.,;:]+$", "", normalized).strip()
        return normalized in {
            "who are you",
            "what is your name",
            "whats your name",
            "what's your name",
            "who are u",
            "what can you do",
        }

    @staticmethod
    def _identity_response() -> str:
        return "I'm Astra, your AI receptionist. I help customers with the verified information and services provided by this receptionist."

    def _finish(self, conversation_id, session_id, response):
        clean = self._clean_response(response)
        self.conversation_service.add_message(conversation_id, "assistant", clean)
        return session_id, clean

    @staticmethod
    def _remove_current_message(messages, current_message):
        normalized = list(messages or [])
        for index in range(len(normalized) - 1, -1, -1):
            item = normalized[index]
            role = item.get("role") if isinstance(item, dict) else getattr(item, "role", None)
            content = item.get("content") if isinstance(item, dict) else getattr(item, "content", None)
            if str(role or "").lower() == "user" and str(content or "").strip() == current_message:
                return normalized[:index] + normalized[index + 1 :]
        return normalized

    @staticmethod
    def _get_active_lead_field(previous_messages):
        for item in reversed(list(previous_messages or [])):
            role = item.get("role") if isinstance(item, dict) else getattr(item, "role", None)
            content = item.get("content") if isinstance(item, dict) else getattr(item, "content", None)
            if str(role or "").lower() == "assistant":
                return LeadContextService.get_requested_field(str(content or ""))
        return None

    @staticmethod
    def _invalid_lead_field_response(field: str) -> str:
        return {
            "email": "Please enter a valid email address, such as name@example.com.",
            "phone": "Please enter a valid 10-digit phone number.",
            "name": "Please enter your name.",
            "preferred_mode": "Please choose online or classroom.",
            "preferred_time": "Please provide a preferred time.",
        }.get(field, "Could you please provide that information?")

    async def _handle_active_lead_field(self, message, lead_context, active_field, conversation_id, organization_id):
        value = None
        if active_field == "name":
            value = self.lead_context_service.extract_name(message) or self.lead_context_service._extract_direct_name_answer(message)
        elif active_field == "phone":
            value = self.lead_context_service.extract_phone(message)
        elif active_field == "email":
            value = self.lead_context_service.extract_email(message)
        elif active_field == "preferred_mode":
            value = self.lead_context_service.extract_preferred_mode(message)
        elif active_field == "preferred_time":
            value = self.lead_context_service.extract_preferred_time(message)
        if value:
            setattr(lead_context, active_field, value)
        lead_context.is_lead = True
        await self._save_lead_context(conversation_id, organization_id, lead_context)
        if lead_context.is_complete:
            return "Thanks. I've captured your details."
        return self.lead_context_service.get_next_question(lead_context) or "Thanks."

    async def _save_lead_context(self, conversation_id, organization_id, lead_context):
        self.lead_service.upsert_lead(
            conversation_id=conversation_id,
            organization_id=organization_id,
            name=lead_context.name,
            phone=lead_context.phone,
            email=lead_context.email,
            interest=lead_context.interest,
            preferred_mode=lead_context.preferred_mode,
            preferred_time=lead_context.preferred_time,
            notes=lead_context.notes,
        )

    @staticmethod
    def _limit_text(text: str, max_chars: int) -> str:
        value = str(text or "")
        return value if len(value) <= max_chars else value[: max_chars - 3].rstrip() + "..."

    @staticmethod
    def _clean_response(response: str | None) -> str:
        text = str(response or "").strip()
        text = re.sub(r"^(?:AI|Astra|Assistant|AI Receptionist)\s*[:\-]\s*", "", text, flags=re.IGNORECASE)
        return text or "I don't currently have that information."

    def _apply_response_length_guard(self, response: str, response_style: str) -> str:
        limits = {
            "short": self.MAX_SHORT_RESPONSE_CHARS,
            "medium": self.MAX_MEDIUM_RESPONSE_CHARS,
            "long": self.MAX_LONG_RESPONSE_CHARS,
        }
        max_chars = limits.get(response_style, self.MAX_MEDIUM_RESPONSE_CHARS)
        return response if len(response) <= max_chars else response[: max_chars - 1].rstrip() + "…"

    @staticmethod
    def _build_missing_information_response(current_subject: str | None) -> str:
        return (
            f"I don't currently have verified information about {current_subject}."
            if current_subject
            else "I don't currently have that information."
        )
