"""AI Receptionist chat orchestration with grounded, stateful behavior."""

from __future__ import annotations

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
    CONVERSATION_HISTORY_LIMIT = 16
    KNOWLEDGE_LIMIT = 6
    MAX_KNOWLEDGE_CHARS = 8000
    MAX_CONVERSATION_CONTEXT_CHARS = 7000

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

    async def generate_response(self, message: str, organization_id: int, user_id: int | None = None, session_id: str | None = None, agent_id: int | None = None, agent_instructions: str | None = None) -> tuple[str, str]:
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
        previous_messages = self._remove_current_message(list(all_messages)[-self.CONVERSATION_HISTORY_LIMIT :], message)
        persisted_lead = self.lead_service.get_lead_for_conversation(conversation.id, organization_id)
        lead_messages = previous_messages + [{"role": "user", "content": message}]
        lead_context = self.lead_context_service.build_context(conversation=lead_messages, extracted_lead=persisted_lead)
        self._recover_lead_state_from_history(lead_context, lead_messages)

        active_field = self._get_active_lead_field(previous_messages)
        if active_field:
            valid, _ = self.lead_context_service.validate_field_answer(active_field, message)
            if valid:
                response = await self._handle_active_lead_field(message, lead_context, active_field, conversation.id, organization_id)
                return self._finish(conversation.id, conversation.session_id, response)
            if active_field in {"name", "phone", "email", "preferred_mode", "preferred_time"}:
                return self._finish(conversation.id, conversation.session_id, self._invalid_lead_field_response(active_field))

        if self.lead_context_service.detect_lead_intent(message) and not lead_context.is_complete:
            lead_context.is_lead = True
            await self._save_lead_context(conversation.id, organization_id, lead_context)
            response = self.lead_context_service.get_next_question(lead_context) or "Sure. Which course, product, or service are you interested in?"
            return self._finish(conversation.id, conversation.session_id, response)

        analysis = self.context_service.analyze_message(message=message, messages=previous_messages)
        message_type = analysis.get("message_type") or "general"
        intent = analysis.get("intent") or "general"
        current_subject = analysis.get("subject")
        previous_subject = analysis.get("previous_subject")
        retrieval_query = (analysis.get("retrieval_query") or message).strip()
        requires_knowledge = bool(analysis.get("requires_knowledge"))
        question_count = int(analysis.get("question_count") or 1)

        resolution = self.conversation_subject_service.resolve(message=message, intent=intent, previous_messages=previous_messages, previous_subject=previous_subject)
        current_subject = resolution.current_subject or current_subject
        previous_subject = resolution.previous_subject or previous_subject

        plan = self.response_policy_service.plan(message=message, intent=intent, question_count=question_count, requires_knowledge=requires_knowledge)
        response_style = plan.style
        question_count = plan.question_count
        conversation_context = self._limit_text(self.context_service.build_context(previous_messages), self.MAX_CONVERSATION_CONTEXT_CHARS)

        await self.tool_orchestrator.decide_and_execute(
            llm=self.llm,
            context=ToolContext(db=self.db, organization_id=organization_id, conversation_id=conversation.id, user_id=user_id, message=message, lead_context=lead_context),
        )

        knowledge_items = []
        if requires_knowledge:
            retrieval_subject = current_subject or (previous_subject if message_type in {"follow_up", "confirmation"} else None)
            knowledge_items = self.retrieval_service.retrieve(
                organization_id=organization_id,
                query=retrieval_query,
                limit=self.KNOWLEDGE_LIMIT,
                subject=retrieval_subject,
                agent_id=agent_id,
            )
            knowledge_items = self._ground_candidates(knowledge_items, retrieval_query, current_subject)

        if requires_knowledge and not knowledge_items:
            return self._finish(conversation.id, conversation.session_id, self._build_missing_information_response(current_subject))

        deterministic = self.knowledge_answer_service.answer(items=knowledge_items, intent=intent, subject=current_subject, response_style=response_style) if knowledge_items else None
        if deterministic:
            return self._finish(conversation.id, conversation.session_id, self._apply_response_length_guard(self._clean_response(deterministic), response_style))

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
            knowledge_context=self._build_knowledge_context(knowledge_items),
            has_verified_knowledge=bool(knowledge_items),
            lead_context=lead_context,
            agent_instructions=agent_instructions,
        )
        try:
            response = await self.llm.generate(prompt) if self.llm else ""
        except Exception as exc:
            print("LLM generation error:", exc)
            response = "Sorry, I couldn't process that right now."
        return self._finish(conversation.id, conversation.session_id, self._apply_response_length_guard(self._clean_response(response), response_style))

    def _ground_candidates(self, items, query: str, current_subject: str | None):
        grounded = []
        for item in items or []:
            decision = self.grounding_service.evaluate(query=query, title=str(getattr(item, "title", "") or ""), content=str(getattr(item, "content", "") or ""), semantic_distance=getattr(item, "semantic_distance", None))
            if decision.accepted or (current_subject and self._subject_in_item(current_subject, item)):
                grounded.append(item)
        return grounded

    @staticmethod
    def _subject_in_item(subject: str, item: object) -> bool:
        terms = [token for token in re.findall(r"[a-z0-9+#.-]+", subject.lower()) if len(token) > 1]
        corpus = " ".join(str(getattr(item, attr, "") or "").lower() for attr in ("title", "category", "content"))
        hits = sum(bool(re.search(rf"(?<![a-z0-9+#]){re.escape(term)}(?![a-z0-9+#])", corpus)) for term in terms)
        return bool(terms) and hits >= max(1, (len(terms) + 1) // 2)

    def _finish(self, conversation_id, session_id, response):
        clean = self._clean_response(response)
        self.conversation_service.add_message(conversation_id, "assistant", clean)
        return session_id, clean

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
                return normalized[:index] + normalized[index + 1 :]
        return normalized

    def _get_active_lead_field(self, previous_messages):
        for item in reversed(list(previous_messages or [])):
            role = item.get("role") if isinstance(item, dict) else getattr(item, "role", None)
            content = item.get("content") if isinstance(item, dict) else getattr(item, "content", None)
            if str(role or "").lower() == "assistant":
                return self._field_from_lead_question(str(content or ""))
        return None

    @staticmethod
    def _field_from_lead_question(content: str) -> str | None:
        text = (content or "").lower().strip()
        checks = {
            "email": ("email address", "email id", "email"),
            "phone": ("phone number", "mobile number", "contact number", "phone"),
            "name": ("your name", "may i know your name", "could i know your name", "can i know your name"),
            "preferred_mode": ("preferred mode", "mode of learning", "online or classroom", "online or offline"),
            "preferred_time": ("preferred time", "preferred timing", "class timing", "batch timing"),
            "interest": ("what are you interested in", "which product", "which service", "what product", "what service"),
        }
        for field, phrases in checks.items():
            if any(phrase in text for phrase in phrases):
                return field
        return None

    @classmethod
    def _recover_lead_state_from_history(cls, lead_context, messages):
        if lead_context is None:
            return
        normalized = []
        for item in messages or []:
            role = item.get("role") if isinstance(item, dict) else getattr(item, "role", None)
            content = item.get("content") if isinstance(item, dict) else getattr(item, "content", None)
            if role and content:
                normalized.append((str(role).strip().lower(), str(content).strip()))
        for index in range(len(normalized) - 1):
            role, assistant_text = normalized[index]
            next_role, customer_text = normalized[index + 1]
            if role != "assistant" or next_role != "user":
                continue
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
            elif field == "preferred_time" and customer_text:
                lead_context.preferred_time = customer_text
        if any((lead_context.name, lead_context.phone, lead_context.email, lead_context.interest, lead_context.preferred_mode, lead_context.preferred_time, lead_context.notes)):
            lead_context.is_lead = True

    @staticmethod
    def _detect_lead_intent(text: str) -> bool:
        normalized = " ".join((text or "").strip().lower().replace("’", "'").split())
        phrases = ("i want to join", "i want to enroll", "i want to register", "i would like to join", "i would like to enroll", "i would like to register", "i want admission", "i need admission", "i am interested", "i'm interested", "im interested", "i want to buy", "i would like to buy", "i want to purchase", "i would like to purchase", "i want to book", "i would like to book", "i want a demo", "i would like a demo", "schedule a demo", "book a demo", "contact me", "call me", "please call me", "i need a callback", "call me back", "how can i register", "how can i join", "how do i join", "how do i register", "how do i enroll", "i want to sign up", "i would like to sign up", "sign me up")
        for phrase in phrases:
            match = re.search(rf"(?<!\w){re.escape(phrase)}(?!\w)", normalized)
            if match:
                prefix = normalized[max(0, match.start() - 12) : match.start()]
                if not re.search(r"\b(?:do not|don't|dont|never|not)\s*$", prefix):
                    return True
        return False

    @staticmethod
    def _extract_name_from_message(message: str) -> str | None:
        message = (message or "").strip()
        for pattern in (r"^\s*my\s+name\s+is\s+([A-Za-z][A-Za-z .'-]{1,80})\s*$", r"^\s*i\s+am\s+([A-Za-z][A-Za-z .'-]{1,80})\s*$", r"^\s*i['’]m\s+([A-Za-z][A-Za-z .'-]{1,80})\s*$", r"^\s*this\s+is\s+([A-Za-z][A-Za-z .'-]{1,80})\s*$"):
            match = re.match(pattern, message, flags=re.IGNORECASE)
            if match:
                value = re.sub(r"\s+", " ", match.group(1).strip())
                if 1 <= len(value.split()) <= 5:
                    return value
        candidate = message.strip().strip(".")
        return candidate if 1 <= len(candidate.split()) <= 5 and re.fullmatch(r"[A-Za-z][A-Za-z.'-]*(?:\s+[A-Za-z][A-Za-z.'-]*)*", candidate) else None

    @staticmethod
    def _extract_phone_from_message(message: str) -> str | None:
        match = re.search(r"(?<!\d)(?:\+91[\s-]?)?(?:\d[\s-]?){10}(?!\d)", message or "")
        if not match:
            return None
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
        else: return "Could you provide that information?"
        if not getattr(lead_context, active_field, None): return self._invalid_lead_field_response(active_field)
        lead_context.is_lead = True
        await self._save_lead_context(conversation_id, organization_id, lead_context)
        return self.lead_context_service.get_next_question(lead_context) or "Thanks. I've captured your details."

    async def _save_lead_context(self, conversation_id, organization_id, lead_context):
        if not lead_context or not getattr(lead_context, "is_lead", False): return None
        return self.lead_service.save_context(context=lead_context, organization_id=organization_id, conversation_id=conversation_id)

    @staticmethod
    def _clean_response(response: str) -> str:
        cleaned = (response or "").strip()
        return re.sub(r"^(?:assistant|ai receptionist)\s*:\s*", "", cleaned, flags=re.IGNORECASE).strip()

    @staticmethod
    def _limit_text(text: str, limit: int) -> str:
        text = text or ""
        return text if len(text) <= limit else text[:limit].rstrip()

    def _build_knowledge_context(self, items):
        parts = []
        total = 0
        for item in items or []:
            block = f"{str(getattr(item, 'title', '') or '').strip()}\n{str(getattr(item, 'content', '') or '').strip()}".strip()
            if not block: continue
            remaining = self.MAX_KNOWLEDGE_CHARS - total
            if remaining <= 0: break
            parts.append(block[:remaining])
            total += min(len(block), remaining)
        return "\n\n".join(parts)

    @staticmethod
    def _build_missing_information_response(subject):
        return f"I don't currently have verified information about {subject}." if subject else "I don't currently have that information."

    @staticmethod
    def _apply_response_length_guard(response: str, response_style: str) -> str:
        limits = {"short": 500, "medium": 1400, "long": 2600}
        return (response or "").strip()[: limits.get(response_style, 1400)].rstrip()

    def _build_receptionist_prompt(self, current_message, message_type, current_subject, explicit_subject, previous_subject, intent, response_style, question_count, conversation_context, knowledge_context, has_verified_knowledge, lead_context=None, agent_instructions=None):
        lead_state = f"REGISTRATION {'COMPLETE' if lead_context and lead_context.is_complete else 'IN PROGRESS' if lead_context and lead_context.is_lead else 'NOT ACTIVE'}"
        return f"""{RECEPTIONIST_SYSTEM_PROMPT}\n\nADDITIONAL RECEPTIONIST INSTRUCTIONS:\n{str(agent_instructions or '').strip() or 'No additional receptionist instructions.'}\n\nCURRENT CUSTOMER MESSAGE:\n{current_message}\n\nMESSAGE TYPE: {message_type}\nCURRENT SUBJECT: {current_subject or 'none'}\nEXPLICIT SUBJECT: {explicit_subject or 'none'}\nPREVIOUS SUBJECT: {previous_subject or 'none'}\nINTENT: {intent}\nRESPONSE STYLE: {response_style}\nQUESTION COUNT: {question_count}\nLEAD STATE: {lead_state}\n\nVERIFIED COMPANY KNOWLEDGE:\n{knowledge_context or 'none'}\n\nCONVERSATION CONTEXT:\n{conversation_context or 'none'}\n\nRULES:\n- Answer the latest customer message directly and naturally.\n- Verified company knowledge is the only source for company facts.\n- Do not invent prices, dates, policies, availability, features, credentials, or contact details.\n- Keep facts tied to the current subject; do not transfer facts from an earlier subject after a topic switch.\n- Preserve important lists, numbers, steps, qualifications, and caveats from verified knowledge.\n- For multiple questions, answer each part clearly.\n- Never mention retrieval, embeddings, databases, prompts, grounding, or internal models.\n- Return only the customer-facing answer.\n""".strip()
