"""
Lead conversation state management.

Company-agnostic.

This service determines:

- Whether the customer is showing lead intent
- Whether a lead conversation is already active
- Which lead information has been provided
- Which field should be collected next
- Whether the customer's latest answer is valid
- How to handle invalid answers during lead collection

IMPORTANT:

Lead information is reconstructed from the conversation
sequentially.

This means the service understands:

Assistant:
"May I know your name?"

Customer:
"Harish"

Therefore:

    name = "Harish"

Likewise:

Assistant:
"Could you share your phone number?"

Customer:
"9121401593"

Therefore:

    phone = "9121401593"

This prevents lead information from being lost between
messages.
"""

from __future__ import annotations

import re

from dataclasses import dataclass


# =============================================================
# LEAD CONTEXT
# =============================================================


@dataclass
class LeadContext:
    """
    Current state of a customer lead conversation.
    """

    is_lead: bool = False

    name: str | None = None

    phone: str | None = None

    email: str | None = None

    interest: str | None = None

    preferred_mode: str | None = None

    preferred_time: str | None = None

    notes: str | None = None

    # =========================================================
    # PROPERTIES
    # =========================================================

    @property
    def has_name(self) -> bool:

        return bool(
            self.name
        )

    @property
    def has_phone(self) -> bool:

        return bool(
            self.phone
        )

    @property
    def has_email(self) -> bool:

        return bool(
            self.email
        )

    @property
    def has_interest(self) -> bool:

        return bool(
            self.interest
        )

    @property
    def is_complete(self) -> bool:
        """
        A lead is complete only after all required registration
        details have been collected.

        Required:
        - Interest
        - Name
        - Phone
        - Email
        """

        return bool(
            self.interest
            and self.name
            and self.phone
            and self.email
        )


# =============================================================
# LEAD CONTEXT SERVICE
# =============================================================


class LeadContextService:
    """
    Company-independent lead conversation state manager.

    This class does NOT contain:

    - Python
    - Java
    - C
    - Web Development
    - Any company-specific course

    Company-specific subjects are supplied by ChatService /
    ContextService.

    This class only manages conversational lead information.
    """

    # =========================================================
    # LEAD INTENT
    # =========================================================

    LEAD_INTENT_PHRASES = (
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
        "i am interested in",
        "i'm interested in",
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

    # =========================================================
    # NAME
    # =========================================================

    NAME_PATTERNS = (
        r"\bmy\s+name\s+is\s+"
        r"([A-Za-z][A-Za-z .'-]{1,80})",

        r"\bi\s+am\s+"
        r"([A-Za-z][A-Za-z .'-]{1,80})",

        r"\bi['’]m\s+"
        r"([A-Za-z][A-Za-z .'-]{1,80})",

        r"\bim\s+"
        r"([A-Za-z][A-Za-z .'-]{1,80})",

        r"\bthis\s+is\s+"
        r"([A-Za-z][A-Za-z .'-]{1,80})",

        r"\bcall\s+me\s+"
        r"([A-Za-z][A-Za-z .'-]{1,80})",
    )

    # =========================================================
    # PHONE
    # =========================================================

    PHONE_PATTERN = re.compile(
        r"(?<!\d)"
        r"(?:\+91[\s-]?)?"
        r"(?:\d[\s-]?){10}"
        r"(?!\d)"
    )

    # =========================================================
    # EMAIL
    # =========================================================

    EMAIL_PATTERN = re.compile(
        r"\b[A-Za-z0-9._%+-]+"
        r"@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    )

    # =========================================================
    # MODE
    # =========================================================

    ONLINE_WORDS = {
        "online",
        "virtual",
        "remote",
    }

    CLASSROOM_WORDS = {
        "classroom",
        "offline",
        "in person",
        "in-person",
    }

    # =========================================================
    # INIT
    # =========================================================

    def __init__(self) -> None:
        pass

    # =========================================================
    # BUILD CONTEXT
    # =========================================================

    def build_context(
        self,
        conversation,
        extracted_lead=None,
    ) -> LeadContext:
        """
        Reconstruct lead state from the conversation.

        The conversation is processed in chronological order.

        This is critical.

        Example:

            USER:
            I want to join Python.

            ASSISTANT:
            May I know your name?

            USER:
            Harish

            ASSISTANT:
            Could you share your phone number?

            USER:
            9121401593

        Result:

            is_lead = True
            name = Harish
            phone = 9121401593
        """

        context = LeadContext()

        # =====================================================
        # 1. LOAD EXISTING EXTRACTED LEAD
        # =====================================================

        self._apply_extracted_lead(
            context=context,
            extracted_lead=extracted_lead,
        )

        # =====================================================
        # 2. NORMALIZE CONVERSATION
        # =====================================================

        messages = (
            self._normalize_messages(
                conversation
            )
        )

        if not messages:

            return context

        # =====================================================
        # 3. PROCESS CONVERSATION SEQUENTIALLY
        # =====================================================

        previous_assistant_message = None

        for item in messages:

            role = item["role"]

            content = item["content"]

            # -------------------------------------------------
            # USER MESSAGE
            # -------------------------------------------------

            if role == "user":

                # ---------------------------------------------
                # Lead intent
                # ---------------------------------------------

                if self.detect_lead_intent(
                    content
                ):

                    context.is_lead = True

                # ---------------------------------------------
                # Explicit information
                # ---------------------------------------------

                self._extract_explicit_information(
                    context=context,
                    message=content,
                )

                # ---------------------------------------------
                # If receptionist asked for a specific field,
                # interpret a simple answer according to that
                # field.
                # ---------------------------------------------

                if (
                    previous_assistant_message
                ):

                    self._apply_answer_to_requested_field(
                        context=context,
                        assistant_message=(
                            previous_assistant_message
                        ),
                        user_message=content,
                    )

            # -------------------------------------------------
            # ASSISTANT MESSAGE
            # -------------------------------------------------

            elif role == "assistant":

                previous_assistant_message = (
                    content
                )

                # An assistant question alone must not activate a
                # lead. A generative model can occasionally ask for a
                # name in an ordinary conversation; treating that as
                # lead intent would trap every later message in an
                # unwanted registration flow. Lead state instead
                # comes from user intent, supplied lead data, or an
                # existing persisted lead.

        # =====================================================
        # 4. FINAL LEAD CHECK
        # =====================================================

        if self._conversation_contains_lead_data(
            context
        ):

            context.is_lead = True

        return context

    # =========================================================
    # APPLY EXISTING LEAD
    # =========================================================

    def _apply_extracted_lead(
        self,
        context: LeadContext,
        extracted_lead,
    ) -> None:
        """
        Merge previously extracted lead information into the
        conversation state.

        IMPORTANT:

        Never overwrite a value already recovered from the
        conversation with None or an empty value.

        The conversation itself is the source of truth for
        sequential lead collection.

        Example:

            conversation state:
                name = "Harish"

            extractor result:
                name = None

        The final state MUST remain:

            name = "Harish"
        """

        if extracted_lead is None:
            return

        fields = (
            "name",
            "phone",
            "email",
            "interest",
            "preferred_mode",
            "preferred_time",
            "notes",
        )

        for field in fields:

            value = self._clean(
                getattr(
                    extracted_lead,
                    field,
                    None,
                )
            )

            if value:
                setattr(
                    context,
                    field,
                    value,
                )

        if any(
            (
                context.name,
                context.phone,
                context.email,
                context.interest,
                context.preferred_mode,
                context.preferred_time,
                context.notes,
            )
        ):
            context.is_lead = True

    # =========================================================
    # EXPLICIT INFORMATION
    # =========================================================

    def _extract_explicit_information(
        self,
        context: LeadContext,
        message: str,
    ) -> None:
        """
        Extract information when the customer explicitly
        provides it.

        Examples:

            My name is Harish
            My phone is 9876543210
            My email is harish@example.com
        """

        # -----------------------------------------------------
        # NAME
        # -----------------------------------------------------

        name = self.extract_name(
            message
        )

        if name:

            context.name = name

        # -----------------------------------------------------
        # PHONE
        # -----------------------------------------------------

        phone = self.extract_phone(
            message
        )

        if phone:

            context.phone = phone

        # -----------------------------------------------------
        # EMAIL
        # -----------------------------------------------------

        email = self.extract_email(
            message
        )

        if email:

            context.email = email

        # -----------------------------------------------------
        # MODE
        # -----------------------------------------------------

        preferred_mode = (
            self.extract_preferred_mode(
                message
            )
        )

        if preferred_mode:

            context.preferred_mode = (
                preferred_mode
            )

        # -----------------------------------------------------
        # TIME
        # -----------------------------------------------------

        preferred_time = (
            self.extract_preferred_time(
                message
            )
        )

        if preferred_time:

            context.preferred_time = (
                preferred_time
            )

    # =========================================================
    # ANSWER TO REQUESTED FIELD
    # =========================================================

    def _apply_answer_to_requested_field(
        self,
        context: LeadContext,
        assistant_message: str,
        user_message: str,
    ) -> None:
        """
        Associate the customer's message with the field the
        receptionist just requested.

        Example:

            Assistant:
            "May I know your name?"

            User:
            "Harish"

        Result:

            context.name = "Harish"
        """

        field = (
            self.get_requested_field(
                assistant_message
            )
        )

        if not field:

            return

        # =====================================================
        # NAME
        # =====================================================

        if field == "name":

            value = (
                self._extract_direct_name_answer(
                    user_message
                )
            )

            if value:

                context.name = value

            return

        # =====================================================
        # PHONE
        # =====================================================

        if field == "phone":

            value = self.extract_phone(
                user_message
            )

            if value:

                context.phone = value

            return

        # =====================================================
        # EMAIL
        # =====================================================

        if field == "email":

            value = self.extract_email(
                user_message
            )

            if value:

                context.email = value

            return

        # =====================================================
        # INTEREST
        # =====================================================

        if field == "interest":

            value = (
                user_message
                or ""
            ).strip()

            if value:

                context.interest = value

            return

        # =====================================================
        # MODE
        # =====================================================

        if field == "preferred_mode":

            value = (
                self.extract_preferred_mode(
                    user_message
                )
            )

            if value:

                context.preferred_mode = (
                    value
                )

            return

        # =====================================================
        # TIME
        # =====================================================

        if field == "preferred_time":

            value = (
                self.extract_preferred_time(
                    user_message
                )
            )

            if value:

                context.preferred_time = (
                    value
                )

    # =========================================================
    # REQUESTED FIELD
    # =========================================================

    @staticmethod
    def get_requested_field(
        assistant_message: str,
    ) -> str | None:
        """
        Determine what the receptionist asked the customer
        to provide.
        """

        text = (
            assistant_message
            or ""
        ).strip().lower()

        if not text:

            return None

        # -----------------------------------------------------
        # EMAIL
        # -----------------------------------------------------

        if (
            "email address" in text
            or "email id" in text
        ):

            return "email"

        if (
            "share your email" in text
            or "provide your email" in text
            or "enter your email" in text
            or "give your email" in text
        ):

            return "email"

        # -----------------------------------------------------
        # PHONE
        # -----------------------------------------------------

        if (
            "phone number" in text
            or "mobile number" in text
            or "contact number" in text
        ):

            return "phone"

        if (
            "share your phone" in text
            or "provide your phone" in text
            or "enter your phone" in text
            or "give your phone" in text
        ):

            return "phone"

        # -----------------------------------------------------
        # NAME
        # -----------------------------------------------------

        if (
            "your name" in text
            or "may i know your name" in text
            or "could i know your name" in text
            or "can i know your name" in text
        ):

            return "name"

        # -----------------------------------------------------
        # INTEREST
        # -----------------------------------------------------

        if (
            "what are you interested in" in text
            or "which product" in text
            or "which service" in text
            or "what product" in text
            or "what service" in text
            or "what would you like to" in text
        ):

            return "interest"

        # -----------------------------------------------------
        # MODE
        # -----------------------------------------------------

        if (
            "online or classroom" in text
            or "online or offline" in text
            or "preferred mode" in text
        ):

            return "preferred_mode"

        # -----------------------------------------------------
        # TIME
        # -----------------------------------------------------

        if (
            "preferred time" in text
            or "preferred timing" in text
            or "what time" in text
        ):

            return "preferred_time"

        return None

    # =========================================================
    # LEAD COLLECTION QUESTION
    # =========================================================

    @classmethod
    def _is_lead_collection_question(
        cls,
        message: str,
    ) -> bool:

        return (
            cls.get_requested_field(
                message
            )
            is not None
        )

    # =========================================================
    # DIRECT NAME ANSWER
    # =========================================================

    def _extract_direct_name_answer(
        self,
        message: str,
    ) -> str | None:
        """
        Extract a name from a direct response to:

            "May I know your name?"

        Supports:

            Harish
            Harish Sadula
            My name is Harish
            I am Harish
            I'm Harish
        """

        message = (
            message or ""
        ).strip()

        if not message:

            return None

        # -----------------------------------------------------
        # Explicit name formats
        # -----------------------------------------------------

        explicit = self.extract_name(
            message
        )

        if explicit:

            return explicit

        # -----------------------------------------------------
        # Simple direct name
        # -----------------------------------------------------

        candidate = (
            message
            .strip()
            .strip(".")
            .strip()
        )

        if not candidate:

            return None

        # -----------------------------------------------------
        # Reject obvious non-name answers.
        # -----------------------------------------------------

        if "@" in candidate:

            return None

        if any(
            character.isdigit()
            for character in candidate
        ):

            return None

        if len(
            candidate
        ) > 80:

            return None

        words = candidate.split()

        if not (
            1
            <= len(words)
            <= 5
        ):

            return None

        for word in words:

            if not re.fullmatch(
                r"[A-Za-z][A-Za-z.'-]*",
                word,
            ):

                return None

        if all(
            len(word) >= 5
            and not re.search(
                r"[aeiou]",
                word,
                flags=re.IGNORECASE,
            )
            for word in words
        ):

            return None

        return candidate

    # =========================================================
    # LEAD DATA CHECK
    # =========================================================

    @staticmethod
    def _conversation_contains_lead_data(
        context: LeadContext,
    ) -> bool:

        return any(
            (
                context.name,
                context.phone,
                context.email,
                context.interest,
                context.preferred_mode,
                context.preferred_time,
                context.notes,
            )
        )

    # =========================================================
    # LEAD INTENT
    # =========================================================

    def detect_lead_intent(
        self,
        text: str,
    ) -> bool:

        normalized = self._normalize(
            text
        )

        if not normalized:

            return False

        for phrase in self.LEAD_INTENT_PHRASES:

            if phrase in normalized:

                return True

        return False

    # =========================================================
    # NAME
    # =========================================================

    def extract_name(
        self,
        text: str,
    ) -> str | None:

        text = (
            text or ""
        )

        for pattern in self.NAME_PATTERNS:

            match = re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )

            if not match:

                continue

            value = (
                match.group(1)
                .strip()
            )

            value = re.sub(
                r"\s+",
                " ",
                value,
            )

            value = re.split(
                r"[.!?,;:]",
                value,
                maxsplit=1,
            )[0].strip()

            if self._looks_like_name(
                value
            ):

                return value

        return None

    # =========================================================
    # PHONE
    # =========================================================

    def extract_phone(
        self,
        text: str,
    ) -> str | None:

        if not text:

            return None

        # -----------------------------------------------------
        # First reject a standalone number that is clearly
        # longer than a valid phone number.
        # -----------------------------------------------------

        compact = re.sub(
            r"[\s-]",
            "",
            text.strip(),
        )

        if (
            compact.isdigit()
            and len(compact) > 10
        ):

            return None

        match = self.PHONE_PATTERN.search(
            text
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
    # EMAIL
    # =========================================================

    def extract_email(
        self,
        text: str,
    ) -> str | None:

        if not text:

            return None

        match = self.EMAIL_PATTERN.search(
            text
        )

        if not match:

            return None

        return (
            match.group(0)
            .lower()
            .strip()
        )

    # =========================================================
    # MODE
    # =========================================================

    def extract_preferred_mode(
        self,
        text: str,
    ) -> str | None:

        normalized = self._normalize(
            text
        )

        if not normalized:

            return None

        for value in self.ONLINE_WORDS:

            if value in normalized:

                return "online"

        for value in self.CLASSROOM_WORDS:

            if value in normalized:

                return "classroom"

        return None

    # =========================================================
    # TIME
    # =========================================================

    def extract_preferred_time(
        self,
        text: str,
    ) -> str | None:

        if not text:

            return None

        patterns = (
            r"\b\d{1,2}(?::\d{2})?\s*"
            r"(?:am|pm)\b",

            r"\b\d{1,2}(?::\d{2})?\s*"
            r"(?:a\.m\.|p\.m\.)\b",
        )

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )

            if match:

                return (
                    match.group(0)
                    .strip()
                )

        normalized = self._normalize(
            text
        )

        for value in (
            "morning",
            "afternoon",
            "evening",
            "night",
        ):

            if value in normalized:

                return value

        return None

    # =========================================================
    # CURRENT / NEXT MISSING FIELD
    # =========================================================

    def get_next_missing_field(
        self,
        context: LeadContext,
    ) -> str | None:
        """
        Determine the next field to collect.

        Order:

        1. Interest
        2. Name
        3. Phone
        4. Email

        Interest is normally supplied by ChatService from the
        active subject.
        """

        if not context.interest:

            return "interest"

        if not context.name:

            return "name"

        if not context.phone:

            return "phone"

        if not context.email:

            return "email"

        return None

    # =========================================================
    # NEXT QUESTION
    # =========================================================

    def get_next_question(
        self,
        context: LeadContext,
    ) -> str | None:

        field = (
            self.get_next_missing_field(
                context
            )
        )

        # -----------------------------------------------------
        # INTEREST
        # -----------------------------------------------------

        if field == "interest":

            return (
                "Sure! What product or service "
                "are you interested in?"
            )

        # -----------------------------------------------------
        # NAME
        # -----------------------------------------------------

        if field == "name":

            return (
                "Sure! May I know your name?"
            )

        # -----------------------------------------------------
        # PHONE
        # -----------------------------------------------------

        if field == "phone":

            if context.name:

                return (
                    f"Thanks, {context.name}! "
                    "Could you share your phone number?"
                )

            return (
                "Sure! Could you share your "
                "phone number?"
            )

        # -----------------------------------------------------
        # EMAIL
        # -----------------------------------------------------

        if field == "email":

            return (
                "Thanks! Could you share your "
                "email address?"
            )

        return None

    # =========================================================
    # INVALID FIELD RESPONSE
    # =========================================================

    def get_invalid_field_response(
        self,
        field: str | None,
        value: str,
    ) -> str | None:

        if field == "email":

            if value.strip():

                return (
                    "Please enter a valid email address, "
                    "such as name@example.com."
                )

            return (
                "Could you share your email address?"
            )

        if field == "phone":

            if value.strip():

                return (
                    "Please enter a valid phone number."
                )

            return (
                "Could you share your phone number?"
            )

        if field == "name":

            if value.strip():

                return (
                    "Sorry, I didn't catch your name. "
                    "Could you please provide it?"
                )

            return (
                "May I know your name?"
            )

        if field == "interest":

            return (
                "Which product or service would "
                "you like to enquire about?"
            )

        return None

    # =========================================================
    # VALIDATE CURRENT ANSWER
    # =========================================================

    def validate_field_answer(
        self,
        field: str | None,
        message: str,
    ) -> tuple[bool, str | None]:
        """
        Validate the customer's latest answer.

        This is used by ChatService when it knows that the
        receptionist is actively collecting a particular field.
        """

        message = (
            message or ""
        ).strip()

        if not message:

            return (
                False,
                None,
            )

        # =====================================================
        # EMAIL
        # =====================================================

        if field == "email":

            value = self.extract_email(
                message
            )

            if value:

                return (
                    True,
                    value,
                )

            return (
                False,
                None,
            )

        # =====================================================
        # PHONE
        # =====================================================

        if field == "phone":

            value = self.extract_phone(
                message
            )

            if value:

                return (
                    True,
                    value,
                )

            return (
                False,
                None,
            )

        # =====================================================
        # NAME
        # =====================================================

        if field == "name":

            value = (
                self._extract_direct_name_answer(
                    message
                )
            )

            if value:

                return (
                    True,
                    value,
                )

            return (
                False,
                None,
            )

        # =====================================================
        # INTEREST
        # =====================================================

        if field == "interest":

            value = (
                message.strip()
            )

            if value:

                return (
                    True,
                    value,
                )

            return (
                False,
                None,
            )

        # =====================================================
        # MODE
        # =====================================================

        if field == "preferred_mode":

            value = (
                self.extract_preferred_mode(
                    message
                )
            )

            if value:

                return (
                    True,
                    value,
                )

            return (
                False,
                None,
            )

        # =====================================================
        # TIME
        # =====================================================

        if field == "preferred_time":

            value = (
                self.extract_preferred_time(
                    message
                )
            )

            if value:

                return (
                    True,
                    value,
                )

            return (
                False,
                None,
            )

        return (
            False,
            None,
        )

    # =========================================================
    # NORMALIZATION
    # =========================================================

    @staticmethod
    def _normalize(
        text: str,
    ) -> str:

        return " ".join(
            (text or "")
            .strip()
            .lower()
            .split()
        )

    # =========================================================
    # MESSAGE NORMALIZATION
    # =========================================================

    @staticmethod
    def _normalize_messages(
        messages,
    ) -> list[dict[str, str]]:
        """
        Normalize SQLAlchemy messages or dictionaries.
        """

        if not messages:

            return []

        result = []

        for message in list(
            messages
        ):

            role = getattr(
                message,
                "role",
                None,
            )

            content = getattr(
                message,
                "content",
                None,
            )

            if isinstance(
                message,
                dict,
            ):

                role = message.get(
                    "role"
                )

                content = message.get(
                    "content"
                )

            if not role or not content:

                continue

            role = str(
                role
            ).strip().lower()

            content = str(
                content
            ).strip()

            if role not in {
                "user",
                "assistant",
            }:

                continue

            if not content:

                continue

            result.append(
                {
                    "role": role,
                    "content": content,
                }
            )

        return result

    # =========================================================
    # CLEAN
    # =========================================================

    @staticmethod
    def _clean(
        value,
    ) -> str | None:

        if value is None:

            return None

        value = str(
            value
        ).strip()

        return value or None

    # =========================================================
    # NAME VALIDATION
    # =========================================================

    @staticmethod
    def _looks_like_name(
        value: str,
    ) -> bool:
        """
        Validate a possible name.

        This intentionally stays simple because this service
        is company-agnostic and should work internationally
        without maintaining a list of names.
        """

        if not value:

            return False

        words = value.split()

        if not (
            1
            <= len(words)
            <= 5
        ):

            return False

        for word in words:

            if not re.fullmatch(
                r"[A-Za-z][A-Za-z.'-]*",
                word,
            ):

                return False

        if all(
            len(word) >= 5
            and not re.search(
                r"[aeiou]",
                word,
                flags=re.IGNORECASE,
            )
            for word in words
        ):

            return False

        return True
