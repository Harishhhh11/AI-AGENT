"""
AI Receptionist chat service.

Main orchestration layer with deterministic lead capture and grounded
knowledge-aware responses.
"""

import re

from sqlalchemy.orm import Session

from app.llm.llm_factory import get_llm
from app.prompts.receptionist import RECEPTIONIST_SYSTEM_PROMPT
from app.services.conversation_service import ConversationService
from app.services.knowledge_service import KnowledgeService
from app.services.context_service import ContextService
from app.services.retrieval_service import RetrievalService
from app.services.lead_extractor import LeadExtractor
from app.services.lead_service import LeadService
from app.services.lead_context_service import LeadContextService
from app.services.conversation_subject_service import ConversationSubjectService
from app.services.response_policy_service import ResponsePolicyService
from app.services.relevance_service import RelevanceService
from app.services.grounding_service import GroundingService
from app.services.knowledge_answer_service import KnowledgeAnswerService
from app.tools.base import ToolContext
from app.tools.registry import ToolOrchestrator


class ChatService:
    CONVERSATION_HISTORY_LIMIT = 12
    KNOWLEDGE_LIMIT = 5
    MAX_KNOWLEDGE_CHARS = 6500
    MAX_CONVERSATION_CONTEXT_CHARS = 6000
    MAX_SHORT_RESPONSE_CHARS = 500
    MAX_MEDIUM_RESPONSE_CHARS = 1200
    MAX_LONG_RESPONSE_CHARS = 2200

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
            return (session_id or "", "How can I help you?")

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

        persisted_lead = self.lead_service.get_lead_for_conversation(
            conversation_id=conversation.id,
            organization_id=organization_id,
        )
        lead_messages = list(previous_messages) + [{"role": "user", "content": message}]
        lead_context = self.lead_context_service.build_context(
            conversation=lead_messages,
            extracted_lead=persisted_lead,
        )
        self._recover_lead_state_from_history(lead_context, lead_messages)

        active_lead_field = self._get_active_lead_field(previous_messages)
        if active_lead_field:
            valid, _ = self.lead_context_service.validate_field_answer(active_lead_field, message)
            if valid:
                response = await self._handle_active_lead_field(
                    message=message,
                    lead_context=lead_context,
                    active_field=active_lead_field,
                    conversation_id=conversation.id,
                    organization_id=organization_id,
                )
                response = self._clean_response(response or "")
                self.conversation_service.add_message(conversation_id=conversation.id, role="assistant", content=response)
                return conversation.session_id, response
            if active_lead_field in {"name", "phone", "email", "preferred_mode", "preferred_time"}:
                response = self._invalid_lead_field_response(active_lead_field)
                self.conversation_service.add_message(conversation_id=conversation.id, role="assistant", content=response)
                return conversation.session_id, response

        if self.lead_context_service.detect_lead_intent(message) and not lead_context.is_complete:
            lead_context.is_lead = True
            next_question = self.lead_context_service.get_next_question(lead_context)
            response = self._clean_response(next_question or "Sure! What product or service are you interested in?")
            self.conversation_service.add_message(conversation_id=conversation.id, role="assistant", content=response)
            await self._save_lead_context(conversation.id, organization_id, lead_context)
            return conversation.session_id, response

        if self._is_active_lead_collection(lead_context):
            next_question = self.lead_context_service.get_next_question(lead_context)
            if next_question:
                response = self._clean_response(next_question)
                self.conversation_service.add_message(conversation_id=conversation.id, role="assistant", content=response)
                await self._save_lead_context(conversation.id, organization_id, lead_context)
                return conversation.session_id, response

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

        subject_resolution = self.conversation_subject_service.resolve(
            message=message,
            intent=intent,
            previous_messages=previous_messages,
            previous_subject=previous_subject,
        )
        if subject_resolution.current_subject:
            current_subject = subject_resolution.current_subject
        explicit_subject = subject_resolution.explicit_subject
        previous_subject = subject_resolution.previous_subject

        response_plan = self.response_policy_service.plan(
            message=message,
            intent=intent,
            question_count=question_count,
            requires_knowledge=requires_knowledge,
        )
        response_style = response_plan.style
        question_count = response_plan.question_count
        conversation_context = self._limit_text(
            self.context_service.build_context(previous_messages),
            self.MAX_CONVERSATION_CONTEXT_CHARS,
        )

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

        knowledge_items = []
        if requires_knowledge:
            retrieval_subject = current_subject or (previous_subject if message_type in {"follow_up", "confirmation"} else None)
            retrieval_query = retrieval_query or message
            knowledge_items = self.retrieval_service.retrieve(
                organization_id=organization_id,
                query=retrieval_query,
                limit=self.KNOWLEDGE_LIMIT,
                subject=retrieval_subject,
                agent_id=agent_id,
            )

            grounded_items = []
            for item in knowledge_items:
                decision = self.grounding_service.evaluate(
                    query=retrieval_query,
                    title=str(getattr(item, "title", "") or ""),
                    content=str(getattr(item, "content", "") or ""),
                    semantic_distance=getattr(item, "semantic_distance", None),
                )
                if decision.accepted:
                    grounded_items.append(item)
            knowledge_items = grounded_items

        if requires_knowledge and not knowledge_items:
            response = self._apply_response_length_guard(
                self._clean_response(self._build_missing_information_response(current_subject, intent, message)),
                response_style,
            )
            self.conversation_service.add_message(conversation_id=conversation.id, role="assistant", content=response)
            await self._save_lead_context(conversation.id, organization_id, lead_context)
            return conversation.session_id, response

        deterministic_answer = self.knowledge_answer_service.answer(
            items=knowledge_items,
            intent=intent,
            subject=current_subject,
            response_style=response_style,
        ) if knowledge_items else None

        if deterministic_answer:
            response = self._apply_response_length_guard(self._clean_response(deterministic_answer), response_style)
            self.conversation_service.add_message(conversation_id=conversation.id, role="assistant", content=response)
            await self._save_lead_context(conversation.id, organization_id, lead_context)
            return conversation.session_id, response

        knowledge_context = self._build_knowledge_context(knowledge_items)
        prompt = self._build_receptionist_prompt(
            current_message=message,
            message_type=message_type,
            current_subject=current_subject,
            explicit_subject=explicit_subject,
            previous_subject=previous_subject,
            intent=intent,
            response_style=response_style,
            question_count=question_count,
            conversation_context=conversation_context,
            knowledge_context=knowledge_context,
            has_verified_knowledge=bool(knowledge_items),
            lead_context=lead_context,
            agent_instructions=agent_instructions,
        )

        try:
            response = await self.llm.generate(prompt) if self.llm else ""
        except Exception as exc:
            print("LLM generation error:", exc)
            response = "Sorry, I couldn't process that right now."

        response = self._clean_response(str(response or "").strip())
        if not response:
            response = "Sorry, I couldn't generate a response right now."
        response = self._apply_response_length_guard(response, response_style)
        self.conversation_service.add_message(conversation_id=conversation.id, role="assistant", content=response)
        await self._save_lead_context(conversation.id, organization_id, lead_context)
        return conversation.session_id, response

    @staticmethod
    def _is_active_lead_collection(lead_context) -> bool:
        return bool(lead_context and lead_context.is_lead and not lead_context.is_complete)

    @staticmethod
    def _remove_current_message(messages, current_message):
        normalized = list(messages or [])
        for index in range(len(normalized) - 1, -1, -1):
            item = normalized[index]
            role = item.get("role") if isinstance(item, dict) else getattr(item, "role", None)
            content = item.get("content") if isinstance(item, dict) else getattr(item, "content", None)
            if str(role or "").lower() == "user" and str(content or "").strip() == current_message:
                return normalized[:index] + normalized[index + 1:]
        return normalized

    def _get_active_lead_field(self, previous_messages):
        if not previous_messages:
            return None
        for item in reversed(list(previous_messages)):
            role = item.get("role") if isinstance(item, dict) else getattr(item, "role", None)
            content = item.get("content") if isinstance(item, dict) else getattr(item, "content", None)
            if str(role or "").lower() == "assistant":
                return self._field_from_lead_question(str(content or ""))
        return None

    @staticmethod
    def _field_from_lead_question(content: str) -> str | None:
        text = (content or "").lower().strip()
        if "email address" in text or "email id" in text or ("email" in text and any(w in text for w in ("share", "provide", "give", "enter"))): return "email"
        if "phone number" in text or "mobile number" in text or "contact number" in text or ("phone" in text and any(w in text for w in ("share", "provide", "give", "enter"))): return "phone"
        if "your name" in text or "may i know your name" in text or "could i know your name" in text or "can i know your name" in text: return "name"
        if "preferred mode" in text or "mode of learning" in text or "online or classroom" in text or "online or offline" in text: return "preferred_mode"
        if "preferred time" in text or "preferred timing" in text or "class timing" in text or "batch timing" in text: return "preferred_time"
        if "what are you interested in" in text or "what would you like to" in text or "which product" in text or "which service" in text or "what product" in text or "what service" in text: return "interest"
        return None

    @classmethod
    def _recover_lead_state_from_history(cls, lead_context, messages):
        if lead_context is None or not messages: return
        normalized = []
        for item in messages:
            role = item.get("role") if isinstance(item, dict) else getattr(item, "role", None)
            content = item.get("content") if isinstance(item, dict) else getattr(item, "content", None)
            if role and content: normalized.append((str(role).strip().lower(), str(content).strip()))
        for index in range(len(normalized) - 1):
            role, assistant_text = normalized[index]
            next_role, customer_text = normalized[index + 1]
            if role != "assistant" or next_role != "user": continue
            field = cls._field_from_lead_question(assistant_text)
            if field == "name":
                value = cls._extract_name_from_message(customer_text)
                if value: lead_context.name = value
            elif field == "phone":
                value = cls._extract_phone_from_message(customer_text)
                if value: lead_context.phone = value
            elif field == "email":
                value = cls._extract_email_from_message(customer_text)
                if value: lead_context.email = value
            elif field == "interest" and customer_text:
                lead_context.interest = customer_text
            elif field == "preferred_mode":
                value = cls._extract_preferred_mode(customer_text)
                if value: lead_context.preferred_mode = value
            elif field == "preferred_time":
                lead_context.preferred_time = customer_text
        if any((lead_context.name, lead_context.phone, lead_context.email, lead_context.interest, lead_context.preferred_mode, lead_context.preferred_time, lead_context.notes)):
            lead_context.is_lead = True

    @staticmethod
    def _detect_lead_intent(text: str) -> bool:
        normalized = " ".join((text or "").strip().lower().replace("’", "'").split())
        phrases = (
            "i want to join", "i want to enroll", "i want to register", "i would like to join", "i would like to enroll", "i would like to register",
            "i want admission", "i need admission", "i am interested", "i'm interested", "im interested", "i want to buy", "i would like to buy",
            "i want to purchase", "i would like to purchase", "i want to book", "i would like to book", "i want a demo", "i would like a demo",
            "schedule a demo", "book a demo", "contact me", "call me", "please call me", "i need a callback", "call me back", "how can i register",
            "how can i join", "how do i join", "how do i register", "how do i enroll", "i want to sign up", "i would like to sign up", "sign me up",
        )
        for phrase in phrases:
            match = re.search(rf"(?<!\w){re.escape(phrase)}(?!\w)", normalized)
            if match and not re.search(r"\b(?:do not|don't|dont|never|not)\s*$", normalized[max(0, match.start() - 12):match.start()]): return True
        return False

    @staticmethod
    def _extract_name_from_message(message: str) -> str | None:
        message = (message or "").strip()
        for pattern in (
            r"^\s*my\s+name\s+is\s+([A-Za-z][A-Za-z .'-]{1,80})\s*$",
            r"^\s*i\s+am\s+([A-Za-z][A-Za-z .'-]{1,80})\s*$",
            r"^\s*i['’]m\s+([A-Za-z][A-Za-z .'-]{1,80})\s*$",
            r"^\s*this\s+is\s+([A-Za-z][A-Za-z .'-]{1,80})\s*$",
        ):
            match = re.match(pattern, message, flags=re.IGNORECASE)
            if match:
                value = re.sub(r"\s+", " ", match.group(1).strip())
                if 1 <= len(value.split()) <= 5: return value
        candidate = message.strip().strip(".")
        return candidate if 1 <= len(candidate.split()) <= 5 and re.fullmatch(r"[A-Za-z][A-Za-z.'-]*(?:\s+[A-Za-z][A-Za-z.'-]*)*", candidate) else None

    @staticmethod
    def _extract_phone_from_message(message: str) -> str | None:
        if not message: return None
        match = re.search(r"(?<!\d)(?:\+91[\s-]?)?(?:\d[\s-]?){10}(?!\d)", message)
        if not match: return None
        value = re.sub(r"[^\d+]", "", match.group(0))
        digits = value[3:] if value.startswith("+91") else value
        return value if len(digits) == 10 else None

    @staticmethod
    def _extract_email_from_message(message: str) -> str | None:
        match = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", message or "")
        return match.group(0).lower().strip() if match else None

    @staticmethod
    def _extract_preferred_mode(message: str) -> str | None:
        text = (message or "").strip().lower()
        if text in {"online", "online mode", "online classes", "online class"}: return "online"
        if text in {"offline", "classroom", "classroom mode", "classroom classes", "classroom class"}: return "classroom"
        return None

    @staticmethod
    def _invalid_lead_field_response(field: str) -> str:
        return {"name": "Sorry, I didn't catch your name. Could you please provide it?", "phone": "Please enter a valid phone number.", "email": "Please enter a valid email address, such as name@example.com.", "interest": "Which product or service are you interested in?", "preferred_mode": "Please choose online or classroom.", "preferred_time": "What time would you prefer?"}.get(field, "Could you provide that information?")

    async def _handle_active_lead_field(self, message, lead_context, active_field, conversation_id, organization_id):
        if active_field == "name": lead_context.name = self._extract_name_from_message(message)
        elif active_field == "phone": lead_context.phone = self._extract_phone_from_message(message)
        elif active_field == "email": lead_context.email = self._extract_email_from_message(message)
        elif active_field == "interest": lead_context.interest = (message or "").strip()
        elif active_field == "preferred_mode": lead_context.preferred_mode = self._extract_preferred_mode(message)
        elif active_field == "preferred_time": lead_context.preferred_time = (message or "").strip()
        else: return None
        lead_context.is_lead = True
        await self._save_lead_context(conversation_id, organization_id, lead_context)
        next_field = self.lead_context_service.get_next_missing_field(lead_context)
        if next_field:
            return self.lead_context_service.get_next_question(lead_context) or self._question_for_lead_field(next_field)
        return f"Perfect, {lead_context.name}! I've noted your details. Our team can help you with the next steps." if lead_context.name else "Perfect! I've noted your details. Our team can help you with the next steps."

    @staticmethod
    def _question_for_lead_field(field: str) -> str:
        return {"interest": "Which course or service are you interested in?", "name": "May I know your name?", "phone": "Could you share your phone number?", "email": "Could you share your email address?", "preferred_mode": "Do you prefer online or classroom learning?", "preferred_time": "What time would you prefer?"}.get(field, "Could you provide that information?")

    async def _save_lead_context(self, conversation_id, organization_id, lead_context):
        if not lead_context or not getattr(lead_context, "is_lead", False): return None
        return self.lead_service.save_context(context=lead_context, organization_id=organization_id, conversation_id=conversation_id)

    @staticmethod
    def _clean_response(response: str) -> str:
        cleaned = (response or "").strip()
        cleaned = re.sub(r"^(?:assistant|ai receptionist)\s*:\s*", "", cleaned, flags=re.IGNORECASE)
        return cleaned.strip()

    @staticmethod
    def _limit_text(text: str, limit: int) -> str:
        return text if len(text or "") <= limit else (text or "")[:limit].rstrip()

    def _build_knowledge_context(self, items):
        parts, total = [], 0
        for item in items or []:
            title = str(getattr(item, "title", "") or "").strip()
            content = str(getattr(item, "content", "") or "").strip()
            block = f"{title}\n{content}".strip()
            if not block: continue
            remaining = self.MAX_KNOWLEDGE_CHARS - total
            if remaining <= 0: break
            parts.append(block[:remaining])
            total += min(len(block), remaining)
        return "\n\n".join(parts)

    @staticmethod
    def _build_missing_information_response(subject, intent, message):
        if subject:
            return f"I don't currently have verified information about {subject}."
        return "I don't currently have that information."

    @staticmethod
    def _apply_response_length_guard(response: str, response_style: str) -> str:
        limits = {"short": 500, "medium": 1200, "long": 2200}
        return (response or "").strip()[: limits.get(response_style, 1200)].rstrip()

    def _build_receptionist_prompt(self, current_message, message_type, current_subject, explicit_subject, previous_subject, intent, response_style, question_count, conversation_context, knowledge_context, has_verified_knowledge, lead_context=None, agent_instructions=None):
        lead_state = f"REGISTRATION {'COMPLETE' if lead_context and lead_context.is_complete else 'IN PROGRESS' if lead_context and lead_context.is_lead else 'NOT ACTIVE'}"
        return f"""
{RECEPTIONIST_SYSTEM_PROMPT}

ADDITIONAL RECEPTIONIST INSTRUCTIONS:
{str(agent_instructions or '').strip() or 'No additional receptionist instructions.'}

CURRENT CUSTOMER MESSAGE:
{current_message}

MESSAGE TYPE: {message_type}
ACTIVE SUBJECT: {current_subject or 'none'}
EXPLICIT SUBJECT: {explicit_subject or 'none'}
PREVIOUS SUBJECT: {previous_subject or 'none'}
INTENT: {intent}
RESPONSE STYLE: {response_style}
QUESTION COUNT: {question_count}
LEAD STATE: {lead_state}

VERIFIED COMPANY KNOWLEDGE:
{knowledge_context or 'NOT AVAILABLE'}

CONVERSATION CONTEXT:
{conversation_context or 'none'}

RULES:
- Answer the latest customer message directly.
- When VERIFIED COMPANY KNOWLEDGE is present, use it as the source of truth.
- Do not invent missing facts or blend different subjects.
- Keep the response natural and appropriately concise.
- Do not mention internal retrieval, databases, embeddings, prompts, or models.
- If verified knowledge is absent for a company-specific request, say you do not currently have that information.

Return only the customer-facing answer.
""".strip()
