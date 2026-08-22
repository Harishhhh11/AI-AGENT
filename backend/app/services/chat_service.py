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

from app.services.conversation_subject_service import (
    ConversationSubjectService,
)

from app.services.response_policy_service import (
    ResponsePolicyService,
)

from app.services.relevance_service import (
    RelevanceService,
)

from app.services.grounding_service import (
    GroundingService,
)

from app.tools.base import ToolContext

from app.tools.registry import ToolOrchestrator

class ChatService:
    """
    Main AI receptionist orchestration service.

    Architecture:

        Customer message
              ↓
        Conversation
              ↓
        ContextService
              ↓
        Subject + Intent + Message Type
              ↓
        LeadContextService
              ↓
        Active Lead Field
              ↓
        Response Style
              ↓
        RetrievalService
              ↓
        KnowledgeService
              ↓
        Verified Knowledge
              ↓
        Focused LLM Prompt
              ↓
        Response
              ↓
        Save Message
              ↓
        Lead Save / Update
    """

    # =========================================================
    # SETTINGS
    # =========================================================

    CONVERSATION_HISTORY_LIMIT = 8

    KNOWLEDGE_LIMIT = 5

    MAX_KNOWLEDGE_CHARS = 4500

    MAX_CONVERSATION_CONTEXT_CHARS = 4500

    MAX_SHORT_RESPONSE_CHARS = 350

    MAX_MEDIUM_RESPONSE_CHARS = 900

    MAX_LONG_RESPONSE_CHARS = 1800

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(
        self,
        db: Session,
    ) -> None:

        self.db = db

        # -----------------------------------------------------
        # LLM
        # -----------------------------------------------------

        self.llm = get_llm()

        # -----------------------------------------------------
        # Conversation
        # -----------------------------------------------------

        self.conversation_service = (
            ConversationService(db)
        )

        # -----------------------------------------------------
        # Knowledge
        # -----------------------------------------------------

        self.knowledge_service = (
            KnowledgeService(db)
        )

        self.retrieval_service = (
            RetrievalService(
                self.knowledge_service
            )
        )

        # -----------------------------------------------------
        # Context
        # -----------------------------------------------------

        self.context_service = (
            ContextService(
                message_limit=(
                    self.CONVERSATION_HISTORY_LIMIT
                )
            )
        )

        # -----------------------------------------------------
        # Phase 2 conversation intelligence
        # -----------------------------------------------------

        self.conversation_subject_service = (
            ConversationSubjectService()
        )

        self.response_policy_service = (
            ResponsePolicyService()
        )

        self.relevance_service = (
            RelevanceService()
        )

        self.grounding_service = (
            GroundingService(
                relevance_service=self.relevance_service
            )
        )

        # -----------------------------------------------------
        # Lead system
        # -----------------------------------------------------

        self.lead_extractor = (
            LeadExtractor()
        )

        self.lead_service = (
            LeadService(db)
        )

        self.lead_context_service = (
            LeadContextService()
        )

        # All side effects pass through this allow-listed boundary.  The
        # lead tool is active now; external providers remain gated until
        # credentials and confirmation rules are configured.
        self.tool_orchestrator = ToolOrchestrator()

    # =========================================================
    # MAIN CHAT FLOW
    # =========================================================

    async def generate_response(
        self,
        message: str,
        organization_id: int,
        user_id: int | None = None,
        session_id: str | None = None,
        agent_id: int | None = None,
        agent_instructions: str | None = None,
    ) -> tuple[str, str]:
        """
        Generate one customer-facing AI receptionist response.

        Lead conversations are handled before normal knowledge
        retrieval so that answers to name, phone and email
        requests are not accidentally treated as FAQ queries.
        """

        # =====================================================
        # 0. CLEAN MESSAGE
        # =====================================================

        message = (
            message or ""
        ).strip()

        if not message:

            return (
                session_id or "",
                "How can I help you?",
            )

        # =====================================================
        # 1. GET / CREATE CONVERSATION
        # =====================================================

        conversation = (
            self.conversation_service
            .get_or_create_conversation(
                session_id=session_id,
                organization_id=organization_id,
                user_id=user_id,
                agent_id=agent_id,
            )
        )

        # =====================================================
        # 2. SAVE CUSTOMER MESSAGE
        # =====================================================

        self.conversation_service.add_message(
            conversation_id=conversation.id,
            role="user",
            content=message,
        )

        # =====================================================
        # 3. LOAD CONVERSATION
        # =====================================================

        all_messages = (
            self.conversation_service
            .get_messages(
                conversation.id
            )
        )

        recent_messages = list(
            all_messages
        )[
            -self.CONVERSATION_HISTORY_LIMIT:
        ]

        # =====================================================
        # 4. REMOVE CURRENT MESSAGE FROM PREVIOUS HISTORY
        # =====================================================

        previous_messages = (
            self._remove_current_message(
                recent_messages,
                message,
            )
        )

        # =====================================================
        # 5. ANALYZE CURRENT MESSAGE
        # =====================================================

        analysis = (
            self.context_service
            .analyze_message(
                message=message,
                messages=previous_messages,
            )
        )

        message_type = (
            analysis.get(
                "message_type"
            )
            or "general"
        )

        current_subject = (
            analysis.get(
                "subject"
            )
        )

        explicit_subject = (
            analysis.get(
                "explicit_subject"
            )
        )

        previous_subject = (
            analysis.get(
                "previous_subject"
            )
        )

        intent = (
            analysis.get(
                "intent"
            )
            or "general"
        )

        response_style = (
            analysis.get(
                "response_style"
            )
            or "short"
        )

        requires_knowledge = bool(
            analysis.get(
                "requires_knowledge",
                False,
            )
        )

        question_count = (
            analysis.get(
                "question_count",
                1,
            )
        )

        retrieval_query = (
            analysis.get(
                "retrieval_query"
            )
            or ""
        ).strip()

        # =====================================================
        # 5A. PHASE 2 SUBJECT RESOLUTION
        # =====================================================

        subject_resolution = (
            self.conversation_subject_service.resolve(
                message=message,
                intent=intent,
                previous_messages=previous_messages,
                previous_subject=previous_subject,
            )
        )

        if subject_resolution.current_subject:
            current_subject = (
                subject_resolution.current_subject
            )

        explicit_subject = (
            subject_resolution.explicit_subject
        )

        previous_subject = (
            subject_resolution.previous_subject
        )

        # =====================================================
        # 5B. PHASE 2 RESPONSE POLICY
        # =====================================================

        response_plan = (
            self.response_policy_service.plan(
                message=message,
                intent=intent,
                question_count=question_count,
                requires_knowledge=requires_knowledge,
            )
        )

        response_style = response_plan.style
        question_count = response_plan.question_count

        # =====================================================
        # 6. BUILD CONVERSATION CONTEXT
        # =====================================================

        conversation_context = (
            self.context_service
            .build_context(
                previous_messages
            )
        )

        conversation_context = (
            self._limit_text(
                conversation_context,
                self.MAX_CONVERSATION_CONTEXT_CHARS,
            )
        )

        # =====================================================
        # 7. BUILD LEAD CONTEXT
        # =====================================================

        lead_messages = list(
            previous_messages
        )

        lead_messages.append(
            {
                "role": "user",
                "content": message,
            }
        )

        # History is intentionally limited, so restore any lead data
        # already persisted for this conversation before rebuilding
        # state from recent messages.
        persisted_lead = (
            self.lead_service
            .get_lead_for_conversation(
                conversation_id=conversation.id,
                organization_id=organization_id,
            )
        )

        lead_context = (
            self.lead_context_service
            .build_context(
                conversation=lead_messages,
                extracted_lead=persisted_lead,
            )
        )

        # =====================================================
        # 7A. RECOVER DETERMINISTIC LEAD STATE
        # =====================================================
        #
        # Lead collection must not depend solely on an LLM
        # extraction pass. Recover values directly from the
        # question/answer sequence so that a valid phone/email
        # can never make an already-known name disappear.
        #

        self._recover_lead_state_from_history(
            lead_context=lead_context,
            messages=lead_messages,
        )

        # Let the model classify explicit action requests separately from
        # customer-facing response generation.  The planner is constrained
        # to registered tools and never executes confirmation-gated external
        # integrations on its own.
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

        # =====================================================
        # 8. RESOLVE LEAD INTEREST
        # =====================================================

        if lead_context.is_lead:

            active_lead_subject = (
                current_subject
                or previous_subject
            )

            if (
                not lead_context.interest
                and active_lead_subject
            ):

                lead_context.interest = (
                    active_lead_subject
                )

        # =====================================================
        # 9. DETERMINE ACTIVE LEAD FIELD
        # =====================================================
        #
        # Example:
        #
        # Assistant:
        # "Could you share your email address?"
        #
        # Customer:
        # "SGSGRSGRG"
        #
        # The message MUST be interpreted as an email answer,
        # not as a general company question.
        #

        active_lead_field = (
            self._get_active_lead_field(
                previous_messages
            )
        )

        # Answers to the field the receptionist just requested always take
        # precedence over subject/knowledge detection.  For example, Python
        # is a valid answer to an interest question and Jimmy is a valid
        # answer to a name question; neither should be sent to retrieval.
        is_valid_active_lead_answer = False
        if active_lead_field:
            (
                is_valid_active_lead_answer,
                _,
            ) = self.lead_context_service.validate_field_answer(
                active_lead_field,
                message,
            )

        # A stale unanswered lead prompt must not hijack a new customer
        # question. For example, after an old "May I know your name?", a
        # customer asking "Which courses do you offer?" should receive the
        # knowledge answer, not another name-validation error. A fresh lead
        # intent is allowed to resume collection normally.
        is_new_lead_intent = self.lead_context_service.detect_lead_intent(
            message
        )
        normalized_current_message = message.lower().strip()
        question_like = (
            "?" in normalized_current_message
            or normalized_current_message.startswith(
                (
                    "what ",
                    "which ",
                    "how ",
                    "do ",
                    "does ",
                    "is ",
                    "are ",
                    "can ",
                    "could ",
                    "when ",
                    "where ",
                )
            )
        )
        is_new_knowledge_question = bool(
            not is_new_lead_intent
            and (
                requires_knowledge
                or intent not in {"general", "lead"}
                or question_like
            )
        )

        if active_lead_field and (
            is_new_lead_intent
            or (
                is_new_knowledge_question
                and not is_valid_active_lead_answer
            )
        ):
            active_lead_field = None

        # =====================================================
        # 10. HANDLE ACTIVE LEAD FIELD
        # =====================================================

        # The current message may fill the final required field.
        # In that case build_context() correctly marks the lead as
        # complete before this block runs.  The pending assistant
        # question is still authoritative, so handle the answer
        # deterministically instead of passing it to the LLM.
        if (
            lead_context.is_lead
            and active_lead_field
        ):

            lead_field_response = (
                await self._handle_active_lead_field(
                    message=message,
                    lead_context=lead_context,
                    active_field=active_lead_field,
                    conversation_id=conversation.id,
                    organization_id=organization_id,
                )
            )

            if lead_field_response:

                response = (
                    self._clean_response(
                        lead_field_response
                    )
                )

                response = (
                    self._apply_response_length_guard(
                        response=response,
                        response_style=response_style,
                    )
                )

                self.conversation_service.add_message(
                    conversation_id=conversation.id,
                    role="assistant",
                    content=response,
                )

                return (
                    conversation.session_id,
                    response,
                )

        # =====================================================
        # 11. LEAD CONVERSATION
        # =====================================================

        if self._is_active_lead_collection(
            lead_context
        ) and not (
            is_new_knowledge_question
            and not is_valid_active_lead_answer
        ):

            lead_question = (
                self.lead_context_service
                .get_next_question(
                    lead_context
                )
            )

            if lead_question:

                response = (
                    self._clean_response(
                        lead_question
                    )
                )

                response = (
                    self._apply_response_length_guard(
                        response=response,
                        response_style=response_style,
                    )
                )

                self.conversation_service.add_message(
                    conversation_id=conversation.id,
                    role="assistant",
                    content=response,
                )

                await self._save_lead_context(
                    conversation_id=conversation.id,
                    organization_id=organization_id,
                    lead_context=lead_context,
                )

                return (
                    conversation.session_id,
                    response,
                )

        # A short acknowledgement after a completed registration is
        # conversational, not a new registration step or a knowledge
        # query. Keep the reply useful and do not echo "ok" back.
        if (
            lead_context.is_complete
            and message_type == "confirmation"
        ):

            response = "You're welcome! How else can I help you?"

            self.conversation_service.add_message(
                conversation_id=conversation.id,
                role="assistant",
                content=response,
            )

            await self._save_lead_context(
                conversation_id=conversation.id,
                organization_id=organization_id,
                lead_context=lead_context,
            )

            return (
                conversation.session_id,
                response,
            )

        # Do not send clearly invalid input through subject retrieval
        # or the LLM with a stale previous subject.
        if message_type == "unclear":

            response = (
                "Could you please clarify what you'd like to know?"
            )

            self.conversation_service.add_message(
                conversation_id=conversation.id,
                role="assistant",
                content=response,
            )

            return (
                conversation.session_id,
                response,
            )

        # =====================================================
        # 12. KNOWLEDGE RETRIEVAL
        # =====================================================

        knowledge_items = []

        if requires_knowledge:

            retrieval_subject = (
                current_subject
            )

            # -------------------------------------------------
            # Follow-up questions inherit previous subject.
            # -------------------------------------------------

            if (
                not retrieval_subject
                and message_type
                in {
                    "follow_up",
                    "confirmation",
                }
            ):

                retrieval_subject = (
                    previous_subject
                )

            # -------------------------------------------------
            # Retrieval fallback.
            # -------------------------------------------------

            if not retrieval_query:

                retrieval_query = (
                    message
                )

            # -------------------------------------------------
            # Organization-scoped retrieval.
            # -------------------------------------------------

            try:

                knowledge_items = (
                    self.retrieval_service
                    .retrieve(
                        organization_id=(
                            organization_id
                        ),
                        query=retrieval_query,
                        limit=self.KNOWLEDGE_LIMIT,
                        subject=retrieval_subject,
                        agent_id=agent_id,
                    )
                )

            except Exception as exc:

                print(
                    "Knowledge retrieval error:",
                    exc,
                )

                knowledge_items = []

        # =====================================================
        # 12A. PHASE 2 RELEVANCE/GROUNDING
        # =====================================================

        if requires_knowledge and knowledge_items:
            grounded_items = []
            for item in knowledge_items:
                decision = self.grounding_service.evaluate(
                    query=retrieval_query or message,
                    title=str(getattr(item, "title", "") or ""),
                    content=str(getattr(item, "content", "") or ""),
                    semantic_distance=getattr(item, "semantic_distance", None),
                )
                if decision.accepted:
                    grounded_items.append(item)
            knowledge_items = grounded_items

        # =====================================================
        # 13. VERIFIED KNOWLEDGE CONTEXT
        # =====================================================

        knowledge_context = (
            self._build_knowledge_context(
                knowledge_items
            )
        )

        # =====================================================
        # 14. HARD GROUNDING
        # =====================================================

        if (
            requires_knowledge
            and not knowledge_items
        ):

            response = (
                self._build_missing_information_response(
                    subject=current_subject,
                    intent=intent,
                    message=message,
                )
            )

            response = (
                self._clean_response(
                    response
                )
            )

            response = (
                self._apply_response_length_guard(
                    response=response,
                    response_style=response_style,
                )
            )

            self.conversation_service.add_message(
                conversation_id=conversation.id,
                role="assistant",
                content=response,
            )

            await self._save_lead_context(
                conversation_id=conversation.id,
                organization_id=organization_id,
                lead_context=lead_context,
            )

            return (
                conversation.session_id,
                response,
            )

        # Straightforward questions about labelled knowledge fields are
        # answered deterministically. This avoids a generative model
        # overlooking a value that was successfully retrieved.
        structured_response = (
            self._build_structured_knowledge_response(
                knowledge_items=knowledge_items,
                intent=intent,
                subject=current_subject,
            )
        )

        if structured_response:

            response = self._apply_response_length_guard(
                response=structured_response,
                response_style=response_style,
            )

            self.conversation_service.add_message(
                conversation_id=conversation.id,
                role="assistant",
                content=response,
            )

            await self._save_lead_context(
                conversation_id=conversation.id,
                organization_id=organization_id,
                lead_context=lead_context,
            )

            return (
                conversation.session_id,
                response,
            )

        # =====================================================
        # 15. BUILD LLM PROMPT
        # =====================================================

        prompt = (
            self._build_receptionist_prompt(
                current_message=message,
                message_type=message_type,
                current_subject=current_subject,
                explicit_subject=explicit_subject,
                previous_subject=previous_subject,
                intent=intent,
                response_style=response_style,
                question_count=question_count,
                conversation_context=(
                    conversation_context
                ),
                knowledge_context=(
                    knowledge_context
                ),
                has_verified_knowledge=bool(
                    knowledge_items
                ),
                lead_context=lead_context,
                agent_instructions=agent_instructions,
            )
        )

        # =====================================================
        # 16. GENERATE RESPONSE
        # =====================================================

        try:

            response = await self.llm.generate(
                prompt
            )

        except Exception as exc:

            print(
                "LLM generation error:",
                exc,
            )

            response = (
                "Sorry, I couldn't process "
                "that right now."
            )

        response = str(
            response or ""
        ).strip()

        # The LLM must not invent a lead-collection step. Personal
        # details are collected only through the deterministic active
        # lead flow above.
        if (
            not self._is_active_lead_collection(
                lead_context
            )
            and self.lead_context_service.get_requested_field(
                response
            )
        ):

            response = (
                "I can help with information about our available "
                "products and services."
            )

        # A completed registration must never be reopened by a
        # generative response. Course questions, confirmations, and
        # other follow-ups should continue as normal conversation.
        if (
            lead_context.is_complete
            and self.lead_context_service.get_requested_field(
                response
            )
        ):

            response = (
                "Your registration details are already complete. "
                "How else can I help you?"
            )

        # =====================================================
        # 17. CLEAN RESPONSE
        # =====================================================

        response = (
            self._clean_response(
                response
            )
        )

        if not response:

            response = (
                "Sorry, I couldn't generate "
                "a response right now."
            )

        # =====================================================
        # 18. RESPONSE LENGTH SAFETY
        # =====================================================

        response = (
            self._apply_response_length_guard(
                response=response,
                response_style=response_style,
            )
        )

        # =====================================================
        # 19. SAVE ASSISTANT MESSAGE
        # =====================================================

        self.conversation_service.add_message(
            conversation_id=conversation.id,
            role="assistant",
            content=response,
        )

        # =====================================================
        # 20. SAVE LEAD CONTEXT
        # =====================================================

        await self._save_lead_context(
            conversation_id=conversation.id,
            organization_id=organization_id,
            lead_context=lead_context,
        )

        # =====================================================
        # 21. RETURN
        # =====================================================

        return (
            conversation.session_id,
            response,
        )

    # =========================================================
    # ACTIVE LEAD STATE
    # =========================================================

    @staticmethod
    def _is_active_lead_collection(
        lead_context,
    ) -> bool:
        """
        Lead collection is active only while required lead
        information is still missing.

        Once the lead is complete, normal receptionist
        conversation resumes.

        This is critical for messages such as:

            "What's the fee?"

        after registration has already been completed.
        """

        if lead_context is None:
            return False

        if not lead_context.is_lead:
            return False

        return not lead_context.is_complete

    # =========================================================
    # ACTIVE LEAD FIELD DETECTION
    # =========================================================

    @staticmethod
    def _get_active_lead_field(
        previous_messages,
    ) -> str | None:
        """
        Determine the lead field requested by the most recent
        assistant lead-collection question.

        The latest assistant lead question is authoritative.
        Older questions are never allowed to override it.
        """

        if not previous_messages:
            return None

        normalized_messages = []

        for item in previous_messages:

            role = getattr(item, "role", None)
            content = getattr(item, "content", None)

            if isinstance(item, dict):
                role = item.get("role")
                content = item.get("content")

            if not role or not content:
                continue

            normalized_messages.append(
                (
                    str(role).strip().lower(),
                    str(content).strip(),
                )
            )

        for role, content in reversed(normalized_messages):

            if role != "assistant":
                continue

            text = content.lower().strip()

            # Email
            if (
                "email address" in text
                or "email id" in text
                or (
                    "email" in text
                    and any(
                        word in text
                        for word in (
                            "share",
                            "provide",
                            "give",
                            "enter",
                        )
                    )
                )
            ):
                return "email"

            # Phone
            if (
                "phone number" in text
                or "mobile number" in text
                or "contact number" in text
                or (
                    "phone" in text
                    and any(
                        word in text
                        for word in (
                            "share",
                            "provide",
                            "give",
                            "enter",
                        )
                    )
                )
            ):
                return "phone"

            # Preferred mode
            if (
                "preferred mode" in text
                or "mode of learning" in text
                or (
                    "online or classroom" in text
                )
                or (
                    "online or offline" in text
                )
            ):
                return "preferred_mode"

            # Preferred time
            if (
                "preferred time" in text
                or "preferred timing" in text
                or "class timing" in text
                or "batch timing" in text
            ):
                return "preferred_time"

            # Name
            if (
                "your name" in text
                or "may i know your name" in text
                or "could i know your name" in text
                or "can i know your name" in text
            ):
                return "name"

            # Interest
            if (
                "what are you interested in" in text
                or "what would you like to" in text
                or "which product" in text
                or "which service" in text
            ):
                return "interest"

            # We reached the latest assistant message and it
            # wasn't a lead question.
            break

        return None

    # =========================================================
    # RECOVER LEAD STATE FROM CONVERSATION
    # =========================================================

    @classmethod
    def _recover_lead_state_from_history(
        cls,
        lead_context,
        messages,
    ) -> None:
        """
        Deterministically recover lead values from the
        assistant-question/customer-answer sequence.

        This is a safety layer around LeadContextService.

        It prevents this failure:

            Name = Jhon
            Phone = 9121401593
            -> Name becomes missing

        It also ensures preferred mode answers such as
        "online" or "offline" are stored as lead data instead
        of being sent to normal knowledge retrieval.
        """

        if lead_context is None:
            return

        if not messages:
            return

        normalized = []

        for item in messages:

            role = getattr(item, "role", None)
            content = getattr(item, "content", None)

            if isinstance(item, dict):
                role = item.get("role")
                content = item.get("content")

            if not role or not content:
                continue

            normalized.append(
                (
                    str(role).strip().lower(),
                    str(content).strip(),
                )
            )

        # Work through each assistant question and the next
        # customer answer.
        for index in range(len(normalized) - 1):

            role, assistant_text = normalized[index]
            next_role, customer_text = normalized[index + 1]

            if role != "assistant":
                continue

            if next_role != "user":
                continue

            field = cls._field_from_lead_question(
                assistant_text
            )

            if not field:
                continue

            value = customer_text.strip()

            if not value:
                continue

            if field == "name":

                extracted = cls._extract_name_from_message(
                    value
                )

                if extracted:
                    lead_context.name = extracted

            elif field == "phone":

                extracted = cls._extract_phone_from_message(
                    value
                )

                if extracted:
                    lead_context.phone = extracted

            elif field == "email":

                extracted = cls._extract_email_from_message(
                    value
                )

                if extracted:
                    lead_context.email = extracted

            elif field == "preferred_mode":

                mode = cls._extract_preferred_mode(
                    value
                )

                if mode:
                    lead_context.preferred_mode = mode

            elif field == "preferred_time":

                if value:
                    lead_context.preferred_time = value

            elif field == "interest":

                if value:
                    lead_context.interest = value

        # Preserve the first explicit lead-intent message as interest when
        # no later field-specific interest answer has supplied it. This makes
        # lead reconstruction robust even when the initial intent was not
        # preceded by an assistant interest question.
        if not lead_context.interest:
            for role, customer_text in normalized:
                if role == "user" and cls._detect_lead_intent(customer_text):
                    lead_context.interest = customer_text
                    break

        if any(
            (
                lead_context.name,
                lead_context.phone,
                lead_context.email,
                lead_context.interest,
                lead_context.preferred_mode,
                lead_context.preferred_time,
                lead_context.notes,
            )
        ):
            lead_context.is_lead = True

    @staticmethod
    def _detect_lead_intent(text: str) -> bool:
        normalized = " ".join(
            (text or "").strip().lower().split()
        )
        if not normalized:
            return False
        phrases = (
            "i want to join",
            "i want to enroll",
            "i want to register",
            "i would like to join",
            "i would like to enroll",
            "i would like to register",
            "i want admission",
            "i need admission",
            "i am interested",
            "i'm interested",
            "im interested",
            "i want to buy",
            "i would like to buy",
            "i want to purchase",
            "i would like to purchase",
            "i want to book",
            "i would like to book",
            "i want a demo",
            "i would like a demo",
            "schedule a demo",
            "book a demo",
            "contact me",
            "call me",
            "please call me",
            "i need a callback",
            "call me back",
            "how can i register",
            "how can i join",
            "how do i join",
            "how do i register",
            "how do i enroll",
            "i want to sign up",
            "i would like to sign up",
            "sign me up",
        )
        return any(phrase in normalized for phrase in phrases)

    @staticmethod
    def _field_from_lead_question(
        content: str,
    ) -> str | None:

        text = (
            content or ""
        ).lower().strip()

        if (
            "email address" in text
            or "email id" in text
            or (
                "email" in text
                and any(
                    word in text
                    for word in (
                        "share",
                        "provide",
                        "give",
                        "enter",
                    )
                )
            )
        ):
            return "email"

        if (
            "phone number" in text
            or "mobile number" in text
            or "contact number" in text
            or (
                "phone" in text
                and any(
                    word in text
                    for word in (
                        "share",
                        "provide",
                        "give",
                        "enter",
                    )
                )
            )
        ):
            return "phone"

        if (
            "preferred mode" in text
            or "mode of learning" in text
            or "online or classroom" in text
            or "online or offline" in text
        ):
            return "preferred_mode"

        if (
            "preferred time" in text
            or "preferred timing" in text
            or "class timing" in text
            or "batch timing" in text
        ):
            return "preferred_time"

        if (
            "your name" in text
            or "may i know your name" in text
            or "could i know your name" in text
            or "can i know your name" in text
        ):
            return "name"

        if (
            "what are you interested in" in text
            or "which product" in text
            or "which service" in text
        ):
            return "interest"

        return None

    @staticmethod
    def _extract_preferred_mode(
        message: str,
    ) -> str | None:

        text = (
            message or ""
        ).strip().lower()

        if text in {
            "online",
            "online mode",
            "online classes",
            "online class",
        }:
            return "online"

        if text in {
            "offline",
            "classroom",
            "classroom mode",
            "classroom classes",
            "classroom class",
        }:
            return "classroom"

        return None

    # =========================================================
    # HANDLE ACTIVE LEAD FIELD
    # =========================================================

    async def _handle_active_lead_field(
        self,
        message: str,
        lead_context,
        active_field: str,
        conversation_id: int,
        organization_id: int,
    ) -> str | None:
        """
        Handle the customer's answer to the currently active
        lead question.

        A successful answer is stored immediately and the next
        lead field is selected deterministically.
        """

        message = (
            message or ""
        ).strip()

        if not message:
            return self._invalid_lead_field_response(
                active_field
            )

        # =====================================================
        # NAME
        # =====================================================

        if active_field == "name":

            value = self._extract_name_from_message(
                message
            )

            if not value:
                return (
                    "Sorry, I didn't catch your name. "
                    "Could you please provide it?"
                )

            lead_context.name = value

        # =====================================================
        # PHONE
        # =====================================================

        elif active_field == "phone":

            value = self._extract_phone_from_message(
                message
            )

            if not value:
                return (
                    "Please enter a valid phone number."
                )

            lead_context.phone = value

        # =====================================================
        # EMAIL
        # =====================================================

        elif active_field == "email":

            value = self._extract_email_from_message(
                message
            )

            if not value:
                return (
                    "Please enter a valid email address, "
                    "such as name@example.com."
                )

            lead_context.email = value

        # =====================================================
        # INTEREST
        # =====================================================

        elif active_field == "interest":

            if not message:
                return (
                    "Which product or service "
                    "are you interested in?"
                )

            lead_context.interest = message

        # =====================================================
        # PREFERRED MODE
        # =====================================================

        elif active_field == "preferred_mode":

            value = self._extract_preferred_mode(
                message
            )

            if not value:
                return (
                    "Please choose online or classroom."
                )

            lead_context.preferred_mode = value

        # =====================================================
        # PREFERRED TIME
        # =====================================================

        elif active_field == "preferred_time":

            lead_context.preferred_time = message

        else:
            return None

        lead_context.is_lead = True

        # Save the newly collected value immediately.
        await self._save_lead_context(
            conversation_id=conversation_id,
            organization_id=organization_id,
            lead_context=lead_context,
        )

        # =====================================================
        # NEXT REQUIRED FIELD
        # =====================================================

        next_field = (
            self.lead_context_service
            .get_next_missing_field(
                lead_context
            )
        )

        if next_field:

            next_question = (
                self.lead_context_service
                .get_next_question(
                    lead_context
                )
            )

            if next_question:
                return next_question

            return self._question_for_lead_field(
                next_field
            )

        # =====================================================
        # LEAD COMPLETE
        # =====================================================

        name = (
            lead_context.name
            or ""
        ).strip()

        if name:
            return (
                f"Perfect, {name}! I've noted your "
                "details. Our team can help you with "
                "the next steps."
            )

        return (
            "Perfect! I've noted your details. "
            "Our team can help you with the next steps."
        )

    @staticmethod
    def _question_for_lead_field(
        field: str,
    ) -> str:

        questions = {
            "interest": (
                "Which course or service "
                "are you interested in?"
            ),
            "name": (
                "May I know your name?"
            ),
            "phone": (
                "Could you share your phone number?"
            ),
            "email": (
                "Could you share your email address?"
            ),
            "preferred_mode": (
                "Do you prefer online or classroom learning?"
            ),
            "preferred_time": (
                "What time would you prefer?"
            ),
        }

        return questions.get(
            field,
            "Could you provide that information?",
        )

    # =========================================================
    # NAME EXTRACTION
    # =========================================================

    @staticmethod
    def _extract_name_from_message(
        message: str,
    ) -> str | None:
        """
        Extract a person's name from a direct answer.

        Supports:

        My name is Rahul
        I am Rahul
        I'm Rahul
        This is Rahul
        Rahul
        Rahul Kumar
        """

        message = (
            message or ""
        ).strip()

        if not message:

            return None

        patterns = (
            r"^\s*my\s+name\s+is\s+"
            r"([A-Za-z][A-Za-z .'-]{1,80})\s*$",

            r"^\s*i\s+am\s+"
            r"([A-Za-z][A-Za-z .'-]{1,80})\s*$",

            r"^\s*i['’]m\s+"
            r"([A-Za-z][A-Za-z .'-]{1,80})\s*$",

            r"^\s*this\s+is\s+"
            r"([A-Za-z][A-Za-z .'-]{1,80})\s*$",
        )

        for pattern in patterns:

            match = re.match(
                pattern,
                message,
                flags=re.IGNORECASE,
            )

            if match:

                value = (
                    match.group(1)
                    .strip()
                )

                value = re.sub(
                    r"\s+",
                    " ",
                    value,
                )

                if (
                    1
                    <= len(
                        value.split()
                    )
                    <= 5
                ):

                    return value

        # -----------------------------------------------------
        # Simple direct name:
        #
        # Rahul
        # Rahul Kumar
        # -----------------------------------------------------

        candidate = (
            message
            .strip()
            .strip(".")
        )

        if (
            1
            <= len(
                candidate.split()
            )
            <= 5
        ):

            if re.fullmatch(
                r"[A-Za-z][A-Za-z.'-]*"
                r"(?:\s+[A-Za-z][A-Za-z.'-]*)*",
                candidate,
            ):

                return candidate

        return None

    # =========================================================
    # PHONE EXTRACTION
    # =========================================================

    @staticmethod
    def _extract_phone_from_message(
        message: str,
    ) -> str | None:
        """
        Extract a valid Indian/international phone number.

        Examples:

        9876543210
        +91 9876543210
        +91-9876543210
        """

        if not message:

            return None

        pattern = re.compile(
            r"(?<!\d)"
            r"(?:\+91[\s-]?)?"
            r"(?:\d[\s-]?){10}"
            r"(?!\d)"
        )

        match = pattern.search(
            message
        )

        if not match:

            return None

        value = re.sub(
            r"[^\d+]",
            "",
            match.group(0),
        )

        if value.startswith(
            "+91"
        ):

            digits = value[3:]

        else:

            digits = value

        if len(digits) != 10:

            return None

        return value

    # =========================================================
    # EMAIL EXTRACTION
    # =========================================================

    @staticmethod
    def _extract_email_from_message(
        message: str,
    ) -> str | None:
        """
        Extract a valid email address.
        """

        if not message:

            return None

        pattern = re.compile(
            r"\b[A-Za-z0-9._%+-]+"
            r"@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
        )

        match = pattern.search(
            message
        )

        if not match:

            return None

        return (
            match.group(0)
            .lower()
            .strip()
        )

    # =========================================================
    # INVALID LEAD FIELD RESPONSE
    # =========================================================

    @staticmethod
    def _invalid_lead_field_response(
        field: str,
    ) -> str:

        if field == "name":

            return (
                "May I know your name?"
            )

        if field == "phone":

            return (
                "Could you share your phone number?"
            )

        if field == "email":

            return (
                "Could you share your email address?"
            )

        if field == "interest":

            return (
                "Which product or service "
                "are you interested in?"
            )

        if field == "preferred_mode":

            return (
                "Do you prefer online or classroom learning?"
            )

        if field == "preferred_time":

            return (
                "What time would you prefer?"
            )

        return (
            "Could you provide that information?"
        )

    # =========================================================
    # BUILD RECEPTIONIST PROMPT
    # =========================================================

    def _build_receptionist_prompt(
        self,
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
        lead_context=None,
        agent_instructions: str | None = None,
    ) -> str:
        """
        Build a focused prompt for the local LLM.

        The application handles state and grounding.

        The LLM handles natural language generation.
        """

        active_subject = (
            current_subject
            or "none"
        )

        verified_state = (
            "AVAILABLE"
            if has_verified_knowledge
            else "NOT AVAILABLE"
        )

        length_instruction = (
            self._response_length_instruction(
                response_style
            )
        )

        lead_state = (
            self._build_lead_context_prompt(
                lead_context
            )
        )

        agent_guidance = (
            str(agent_instructions or "").strip()
            or "No additional receptionist instructions."
        )

        return f"""
{RECEPTIONIST_SYSTEM_PROMPT}

============================================================
ROLE
============================================================

You are a professional AI receptionist.

Answer the customer naturally and directly.

You are NOT a general-purpose company knowledge generator.

For company-specific facts, use ONLY the VERIFIED COMPANY
KNOWLEDGE provided below.

ADDITIONAL RECEPTIONIST INSTRUCTIONS
{agent_guidance}

============================================================
CURRENT CUSTOMER MESSAGE
============================================================

{current_message}

============================================================
CONVERSATION UNDERSTANDING
============================================================

MESSAGE TYPE:
{message_type}

ACTIVE SUBJECT:
{active_subject}

EXPLICIT SUBJECT:
{explicit_subject or "none"}

PREVIOUS SUBJECT:
{previous_subject or "none"}

INTENT:
{intent}

QUESTION COUNT:
{question_count}

RESPONSE STYLE:
{response_style}

============================================================
LEAD STATE
============================================================

{lead_state}

============================================================
VERIFIED KNOWLEDGE STATUS
============================================================

{verified_state}

============================================================
VERIFIED COMPANY KNOWLEDGE
============================================================

{knowledge_context}

============================================================
CONVERSATION CONTEXT
============================================================

{conversation_context}

============================================================
CRITICAL GROUNDING RULES
============================================================

1. Answer ONLY the customer's CURRENT message.

2. Do not answer an older question.

3. Do not repeat the customer's question.

4. Do not ask the customer's question back.

5. Do not invent company information.

6. Do not guess missing fees, timings, topics, duration,
   courses, products, services, policies, or other facts.

7. Never use information from one subject to answer another
   subject.

8. If verified knowledge is available, use it.

9. If verified knowledge is unavailable, say so naturally.

10. Previous assistant messages are conversation context only.
    They are NOT authoritative company knowledge.

============================================================
SUBJECT HANDLING
============================================================

The ACTIVE SUBJECT is the subject currently being discussed.

If the customer asks a follow-up such as:

"How much?"

"What topics?"

"What is the duration?"

"What are the timings?"

"Is it online?"

then answer for the ACTIVE SUBJECT.

If the customer explicitly changes subject, switch immediately.

Example:

Customer:
Do you offer Python?

Active subject:
Python

Customer:
What about Java?

New active subject:
Java

Customer:
How much?

Answer the Java fee ONLY if verified Java knowledge exists.

If Java knowledge does not exist, do NOT use Python's fee.

============================================================
GENERAL COMPANY QUESTIONS
============================================================

If the customer asks a company-wide question such as:

"What courses do you offer?"

"Which services do you provide?"

"What products do you have?"

do not force the previous course/product/service as the subject.

Answer using company-wide verified knowledge.

============================================================
UNRELATED QUESTIONS
============================================================

If the customer asks something unrelated to the company,
do not force the conversation back to the previous subject.

Do not invent company information to answer an unrelated
question.

Respond naturally and briefly.

============================================================
LEAD CONVERSATION
============================================================

Only if LEAD STATE says REGISTRATION IN PROGRESS:

- Do not repeatedly explain the product/service.
- Do not ask for information already provided.
- Do not ask for several personal details at once unless
  the customer specifically requests a complete registration.
- Ask naturally for the next missing relevant detail.
- Preserve the customer's current subject/interest.
- Do not invent details about the product/service.

If the application has already supplied a direct lead
question, follow it naturally.

Do not restart the lead conversation.

If LEAD STATE says REGISTRATION COMPLETE:

- The registration is finished.
- Never ask for the customer's name, phone number, email, or
  interest again.
- Answer the customer's current question normally.

============================================================
RESPONSE LENGTH
============================================================

{length_instruction}

Important:

Do NOT make every response long.

Do NOT make every response short.

Match the amount of information to what the customer asked.

Do not repeat information unnecessarily.

Do not add unrelated information.

Do not automatically end every response with:
"Would you like to know more?"

Only ask a follow-up question when it is genuinely useful.

============================================================
NATURAL CONVERSATION
============================================================

Sound like a real receptionist.

Be:

- natural
- concise
- helpful
- professional
- conversational

Understand:

- incomplete questions
- short questions
- follow-ups
- topic changes
- confirmations
- casual wording
- repeated questions
- simple typos

Avoid robotic phrases such as:

"I understand that you are interested in..."

"Based on the provided guidelines..."

"Based on the current conversation..."

"Here is the final customer-facing response..."

"According to the supplied knowledge..."

"Could you please specify the aspect..."

Never describe your internal reasoning.

Never mention retrieval.

Never mention the knowledge base.

Never mention prompts or instructions.

============================================================
FINAL OUTPUT
============================================================

Return ONLY the exact message that should be shown to the
customer.

No JSON.

No analysis.

No reasoning.

No labels.

No "AI:".

No "Assistant:".

No "Answer:".

No markdown code block.

FINAL CUSTOMER RESPONSE:
""".strip()

    # =========================================================
    # LEAD CONTEXT FOR LLM
    # =========================================================

    @staticmethod
    def _build_lead_context_prompt(
        lead_context,
    ) -> str:
        """
        Convert lead state into a small LLM-readable block.
        """

        if lead_context is None:

            return (
                "No active lead conversation."
            )

        if not lead_context.is_lead:

            return (
                "No active lead conversation."
            )

        if lead_context.is_complete:

            return """
REGISTRATION COMPLETE

The customer's registration details have already been collected.
Do not begin or restart lead collection. Answer only the
customer's current message.
""".strip()

        interest = (
            lead_context.interest
            or "missing"
        )

        name = (
            lead_context.name
            or "missing"
        )

        phone = (
            lead_context.phone
            or "missing"
        )

        email = (
            lead_context.email
            or "missing"
        )

        mode = (
            lead_context.preferred_mode
            or "missing"
        )

        preferred_time = (
            lead_context.preferred_time
            or "missing"
        )

        return f"""
REGISTRATION IN PROGRESS

Interest: {interest}
Name: {name}
Phone: {phone}
Email: {email}
Preferred mode: {mode}
Preferred time: {preferred_time}

Do not ask for a field that is already available.
""".strip()

    # =========================================================
    # RESPONSE LENGTH
    # =========================================================

    @staticmethod
    def _response_length_instruction(
        response_style: str,
    ) -> str:

        style = (
            response_style
            or "short"
        ).strip().lower()

        if style == "short":

            return """
SHORT RESPONSE.

Give only the information directly needed.

Prefer ONE sentence.

Use at most TWO short sentences if necessary.

Examples:

Customer:
"How much?"

Good:
"The verified fee is available in the company knowledge."

Customer:
"Do you offer Python?"

Good:
"Yes, Python Programming is available online and in the classroom."

Do NOT provide course topics, timings, duration, admission
details, or other information unless the customer asked for
them.
""".strip()

        if style == "medium":

            return """
MEDIUM RESPONSE.

Give the relevant information clearly.

Use approximately 1–3 concise sentences, or a short list
when the information naturally consists of multiple items.

Do not include unrelated information.

For a topic/syllabus question, a compact list is appropriate.

Do not turn a normal question into a long explanation.
""".strip()

        return """
DETAILED RESPONSE.

Provide the requested information clearly and completely.

Use short sections or bullets when useful.

Include only information relevant to the customer's request
and only information supported by VERIFIED COMPANY KNOWLEDGE.

Do not add unrelated information.

Do not repeat the same fact in different ways.
""".strip()

    # =========================================================
    # STRUCTURED KNOWLEDGE RESPONSES
    # =========================================================

    @staticmethod
    def _build_structured_knowledge_response(
        knowledge_items,
        intent: str,
        subject: str | None,
    ) -> str | None:
        """
        Return a direct response for a labelled knowledge field.

        This supports records written in common formats such as
        ``Fee: 8000`` or ``Batch timings:\n10 AM - 11 AM`` while
        leaving unstructured knowledge to the LLM.
        """

        field_labels = {
            "fee": ("fee", "fees", "price", "cost"),
            "duration": ("duration", "course duration"),
            "timings": (
                "batch timings",
                "batch timing",
                "timings",
                "timing",
                "schedule",
            ),
            "admission": (
                "admission",
                "admissions",
                "registration",
                "enrollment",
                "enrolment",
            ),
            "mode": ("availability", "mode", "delivery mode"),
        }

        labels = field_labels.get(intent)

        if not labels:
            return None

        for item in knowledge_items or []:

            content = str(
                getattr(item, "content", "")
                or ""
            )

            value = ChatService._extract_labelled_value(
                content=content,
                labels=labels,
            )

            if not value:
                continue

            subject_text = (
                str(subject or "").strip().title()
            )

            if intent == "fee":

                return (
                    f"The fee"
                    f"{' for ' + subject_text if subject_text else ''} "
                    f"is {value}."
                )

            if intent == "duration":

                return (
                    f"The duration"
                    f"{' of ' + subject_text if subject_text else ''} "
                    f"is {value}."
                )

            if intent == "timings":

                return (
                    f"The batch timings"
                    f"{' for ' + subject_text if subject_text else ''} "
                    f"are {value}."
                )

            if intent == "admission":

                return (
                    f"Admissions"
                    f"{' for ' + subject_text if subject_text else ''} "
                    f"{value}."
                )

            if intent == "mode":

                return (
                    f"Availability"
                    f"{' for ' + subject_text if subject_text else ''}: "
                    f"{value}."
                )

        return None

    @staticmethod
    def _extract_labelled_value(
        content: str,
        labels: tuple[str, ...],
    ) -> str | None:
        """Extract the first non-empty value following a field label."""

        lines = [
            line.strip()
            for line in str(content or "").splitlines()
        ]

        normalized_labels = {
            " ".join(label.lower().split())
            for label in labels
        }

        for index, line in enumerate(lines):

            match = re.match(
                r"^\s*([^:]+?)\s*:\s*(.*)$",
                line,
            )

            if not match:
                continue

            label = " ".join(
                match.group(1).lower().split()
            )

            if label not in normalized_labels:
                continue

            value = match.group(2).strip()

            if value:
                return value

            # Support a label on its own line, with its value directly
            # below it. Stop at the next labelled field.
            for next_line in lines[index + 1:]:

                if not next_line:
                    continue

                if re.match(
                    r"^\s*[^:]{1,80}:\s*",
                    next_line,
                ):

                    break

                return next_line

        return None

    # =========================================================
    # MISSING INFORMATION
    # =========================================================

    @staticmethod
    def _build_missing_information_response(
        subject: str | None,
        intent: str,
        message: str,
    ) -> str:
        """
        Safe deterministic response when company knowledge is
        unavailable.
        """

        subject_text = (
            str(
                subject or ""
            ).strip()
        )

        display_subject = (
            subject_text.title()
            if subject_text
            else ""
        )

        # When a customer asks about two short alternatives (for
        # example, "Java and C"), subject extraction retains both
        # terms for retrieval. Make the unavailable-information reply
        # read naturally without weakening matching for multi-word
        # subjects such as "web development".
        subject_words = subject_text.split()

        if (
            len(subject_words) == 2
            and re.search(
                r"\b(?:and|or)\b",
                message or "",
                flags=re.IGNORECASE,
            )
        ):

            display_subject = " or ".join(
                word.title()
                for word in subject_words
            )

        if intent == "fee":

            if display_subject:

                return (
                    f"I don't currently have the "
                    f"{display_subject} fee information."
                )

            return (
                "I don't currently have the fee "
                "information."
            )

        if intent == "discount":

            if display_subject:

                return (
                    f"I don't currently have verified discount "
                    f"information for {display_subject}."
                )

            return (
                "I don't currently have verified discount "
                "information."
            )

        if intent == "topics":

            if display_subject:

                return (
                    f"I don't currently have verified "
                    f"information about the {display_subject} "
                    f"course topics."
                )

            return (
                "I don't currently have verified "
                "information about the topics."
            )

        if intent == "duration":

            if display_subject:

                return (
                    f"I don't currently have the "
                    f"{display_subject} course duration."
                )

            return (
                "I don't currently have the course "
                "duration information."
            )

        if intent == "timings":

            if display_subject:

                return (
                    f"I don't currently have the "
                    f"{display_subject} batch timings."
                )

            return (
                "I don't currently have the batch "
                "timing information."
            )

        if intent == "duration_and_timings":

            if display_subject:

                return (
                    f"I don't currently have the "
                    f"{display_subject} duration and "
                    f"timing information."
                )

            return (
                "I don't currently have the duration "
                "and timing information."
            )

        if intent == "mode":

            if display_subject:

                return (
                    f"I don't currently have verified "
                    f"information about the {display_subject} "
                    f"course mode."
                )

            return (
                "I don't currently have verified "
                "information about the available modes."
            )

        if intent == "admission":

            if display_subject:

                return (
                    f"I don't currently have the "
                    f"{display_subject} admission information."
                )

            return (
                "I don't currently have the admission "
                "information."
            )

        if intent == "contact":

            return (
                "I don't currently have the requested "
                "contact information."
            )

        if intent == "company_courses":

            return (
                "I don't currently have a verified list of "
                "available courses."
            )

        if intent == "availability":

            if display_subject:

                return (
                    f"I don't currently have verified "
                    f"information about {display_subject}."
                )

            return (
                "I don't currently have verified "
                "information about that."
            )

        if display_subject:

            return (
                f"I don't currently have verified "
                f"information about {display_subject}."
            )

        return (
            "I don't currently have verified "
            "information about that."
        )

    # =========================================================
    # KNOWLEDGE CONTEXT
    # =========================================================

    def _build_knowledge_context(
        self,
        knowledge_items,
    ) -> str:

        if not knowledge_items:

            return (
                "NO VERIFIED COMPANY KNOWLEDGE WAS FOUND."
            )

        sections = []

        remaining_chars = (
            self.MAX_KNOWLEDGE_CHARS
        )

        for index, item in enumerate(
            knowledge_items,
            start=1,
        ):

            title = str(
                getattr(
                    item,
                    "title",
                    "",
                )
                or ""
            ).strip()

            category = str(
                getattr(
                    item,
                    "category",
                    "",
                )
                or ""
            ).strip()

            source = str(
                getattr(
                    item,
                    "source",
                    "",
                )
                or ""
            ).strip()

            content = str(
                getattr(
                    item,
                    "content",
                    "",
                )
                or ""
            ).strip()

            if not content:

                continue

            section = (
                f"SOURCE {index}\n"
                f"TITLE: {title}\n"
                f"CATEGORY: {category}\n"
                f"SOURCE TYPE: {source}\n"
                f"CONTENT:\n{content}"
            )

            if len(
                section
            ) > remaining_chars:

                if remaining_chars <= 0:

                    break

                section = (
                    section[
                        :remaining_chars
                    ]
                    + "\n[truncated]"
                )

            sections.append(
                section
            )

            remaining_chars -= len(
                section
            )

            if remaining_chars <= 0:

                break

        if not sections:

            return (
                "NO VERIFIED COMPANY KNOWLEDGE WAS FOUND."
            )

        return "\n\n".join(
            sections
        )

    # =========================================================
    # TEXT LIMIT
    # =========================================================

    @staticmethod
    def _limit_text(
        text: str,
        maximum: int,
    ) -> str:

        text = str(
            text or ""
        ).strip()

        if len(
            text
        ) <= maximum:

            return text

        return (
            text[
                :maximum
            ]
            + "\n[truncated]"
        )

    # =========================================================
    # RESPONSE LENGTH GUARD
    # =========================================================

    def _apply_response_length_guard(
        self,
        response: str,
        response_style: str,
    ) -> str:

        response = str(
            response or ""
        ).strip()

        if not response:

            return response

        style = (
            response_style
            or "short"
        ).strip().lower()

        if style == "short":

            maximum = (
                self.MAX_SHORT_RESPONSE_CHARS
            )

        elif style == "medium":

            maximum = (
                self.MAX_MEDIUM_RESPONSE_CHARS
            )

        else:

            maximum = (
                self.MAX_LONG_RESPONSE_CHARS
            )

        if len(
            response
        ) <= maximum:

            return response

        shortened = (
            response[
                :maximum
            ]
        )

        sentence_end = max(
            shortened.rfind("."),
            shortened.rfind("?"),
            shortened.rfind("!"),
        )

        if sentence_end >= int(
            maximum * 0.45
        ):

            shortened = shortened[
                : sentence_end + 1
            ]

        else:

            shortened = (
                shortened[
                    : max(0, maximum - 3)
                ].rstrip()
                + "..."
            )

        return shortened.strip()

    # =========================================================
    # CLEAN RESPONSE
    # =========================================================

    @staticmethod
    def _clean_response(
        response: str,
    ) -> str:

        response = str(
            response or ""
        ).strip()

        if not response:

            return ""

        prefixes = (
            "AI RECEPTIONIST:",
            "AI Receptionist:",
            "ASSISTANT:",
            "Assistant:",
            "CUSTOMER-FACING RESPONSE:",
            "Customer-facing response:",
            "FINAL CUSTOMER RESPONSE:",
            "FINAL RESPONSE:",
            "Final Response:",
            "ANSWER:",
            "Answer:",
        )

        changed = True

        while changed:

            changed = False

            for prefix in prefixes:

                if response.startswith(
                    prefix
                ):

                    response = (
                        response[
                            len(prefix):
                        ]
                        .strip()
                    )

                    changed = True

        if response.startswith(
            "```"
        ):

            response = (
                response
                .replace(
                    "```text",
                    "",
                    1,
                )
                .replace(
                    "```",
                    "",
                )
                .strip()
            )

        response = re.sub(
            r"^(final\s+answer|final\s+response)"
            r"\s*:\s*",
            "",
            response,
            flags=re.IGNORECASE,
        ).strip()

        return response

    # =========================================================
    # REMOVE CURRENT MESSAGE
    # =========================================================

    @staticmethod
    def _remove_current_message(
        messages,
        current_message: str,
    ) -> list:

        if not messages:

            return []

        result = list(
            messages
        )

        if not result:

            return []

        last = result[-1]

        last_role = getattr(
            last,
            "role",
            None,
        )

        last_content = getattr(
            last,
            "content",
            None,
        )

        if isinstance(
            last,
            dict,
        ):

            last_role = last.get(
                "role"
            )

            last_content = last.get(
                "content"
            )

        last_role = str(
            last_role or ""
        ).strip().lower()

        last_content = str(
            last_content or ""
        ).strip()

        current_normalized = (
            " ".join(
                str(
                    current_message
                    or ""
                )
                .lower()
                .split()
            )
        )

        last_normalized = (
            " ".join(
                last_content
                .lower()
                .split()
            )
        )

        if (
            last_role == "user"
            and last_normalized
            == current_normalized
        ):

            return result[:-1]

        return result

    # =========================================================
    # SAVE LEAD CONTEXT
    # =========================================================

    async def _save_lead_context(
        self,
        conversation_id: int,
        organization_id: int,
        lead_context,
    ) -> None:
        """
        Save deterministic lead information.

        Lead failures never break the customer conversation.
        """

        try:

            if lead_context is None:

                return

            if not lead_context.is_lead:

                return

            has_information = any(
                (
                    lead_context.name,
                    lead_context.phone,
                    lead_context.email,
                    lead_context.interest,
                    lead_context.preferred_mode,
                    lead_context.preferred_time,
                    lead_context.notes,
                )
            )

            if not has_information:

                return

            tool_context = ToolContext(
                db=self.db,
                organization_id=organization_id,
                conversation_id=conversation_id,
                message="",
                lead_context=lead_context,
            )

            result = await self.tool_orchestrator.execute(
                name="save_lead",
                context=tool_context,
            )

            if not result.success:
                print("SaveLeadTool error:", result.error or result.message)

            # GoogleSheetTool is idempotent and therefore safe to run after
            # every lead update. It updates the conversation row when one
            # exists and appends a row for a first-time lead.
            persisted_lead = self.lead_service.get_lead_for_conversation(
                conversation_id=conversation_id,
                organization_id=organization_id,
            )
            if persisted_lead is not None:
                sheet_context = ToolContext(
                    db=self.db,
                    organization_id=organization_id,
                    conversation_id=conversation_id,
                    message="",
                    lead_context=lead_context,
                    metadata={"lead": persisted_lead},
                )
                sheet_result = await self.tool_orchestrator.execute(
                    name="google_sheet",
                    context=sheet_context,
                )
                if not sheet_result.success:
                    print("GoogleSheetTool:", sheet_result.error or sheet_result.message)
                else:
                    print("GoogleSheetTool synced:", sheet_result.data)

                crm_result = await self.tool_orchestrator.execute(
                    name="crm_sync",
                    context=sheet_context,
                )
                if not crm_result.success:
                    print("CRMSyncTool:", crm_result.error or crm_result.message)
                else:
                    print("CRMSyncTool synced:", crm_result.data)

        except Exception as exc:

            print(
                "Lead save error:",
                exc,
            )

    # =========================================================
    # LEGACY LEAD PROCESSING
    # =========================================================

    async def _process_lead(
        self,
        conversation_id: int,
        organization_id: int,
    ) -> None:
        """
        Backward-compatible lead processing entry point.

        The main chat flow now uses LeadContextService directly.
        """

        try:

            messages = (
                self.conversation_service
                .get_messages(
                    conversation_id
                )
            )

            recent_messages = list(
                messages
            )[
                -self.CONVERSATION_HISTORY_LIMIT:
            ]

            lead_context = (
                self.lead_context_service
                .build_context(
                    conversation=recent_messages
                )
            )

            if not lead_context.is_lead:

                return

            await self._save_lead_context(
                conversation_id=conversation_id,
                organization_id=organization_id,
                lead_context=lead_context,
            )

        except Exception as exc:

            print(
                "Lead processing error:",
                exc,
            )
