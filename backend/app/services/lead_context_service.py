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
"""

from __future__ import annotations

import re

from dataclasses import dataclass


@dataclass
class LeadContext:
    is_lead: bool = False
    name: str | None = None
    phone: str | None = None
    email: str | None = None
    interest: str | None = None
    preferred_mode: str | None = None
    preferred_time: str | None = None
    notes: str | None = None

    @property
    def has_name(self) -> bool:
        return bool(self.name)

    @property
    def has_phone(self) -> bool:
        return bool(self.phone)

    @property
    def has_email(self) -> bool:
        return bool(self.email)

    @property
    def has_interest(self) -> bool:
        return bool(self.interest)

    @property
    def is_complete(self) -> bool:
        return bool(
            self.interest
            and self.name
            and self.phone
            and self.email
        )


class LeadContextService:
    LEAD_INTENT_PHRASES = (
        "i want to join", "i want to enroll", "i want to register",
        "i would like to join", "i would like to enroll", "i would like to register",
        "i want admission", "i need admission", "i am interested", "i'm interested",
        "im interested", "i am interested in", "i'm interested in", "i want to buy",
        "i would like to buy", "i want to purchase", "i would like to purchase",
        "i want to book", "i would like to book", "i want a demo", "i would like a demo",
        "schedule a demo", "book a demo", "contact me", "call me", "please call me",
        "i need a callback", "call me back", "how can i register", "how can i join",
        "how do i join", "how do i register", "how do i enroll", "i want to sign up",
        "i would like to sign up", "sign me up",
    )

    NAME_PATTERNS = (
        r"\bmy\s+name\s+is\s+([A-Za-z][A-Za-z .'-]{1,80})",
        r"\bi\s+am\s+([A-Za-z][A-Za-z .'-]{1,80})",
        r"\bi['’]m\s+([A-Za-z][A-Za-z .'-]{1,80})",
        r"\bim\s+([A-Za-z][A-Za-z .'-]{1,80})",
        r"\bthis\s+is\s+([A-Za-z][A-Za-z .'-]{1,80})",
        r"\bcall\s+me\s+([A-Za-z][A-Za-z .'-]{1,80})",
    )

    NON_NAME_PREFIXES = (
        "interested", "looking", "trying", "planning", "seeking", "calling",
        "enquiring", "inquiring", "contacting", "joining", "enrolling",
        "registering", "buying", "purchasing", "booking", "requesting",
        "searching", "wondering", "hoping", "checking",
    )

    PHONE_PATTERN = re.compile(
        r"(?<!\d)(?:\+91[\s-]?)?(?:\d[\s-]?){10}(?!\d)"
    )
    EMAIL_PATTERN = re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    )
    ONLINE_WORDS = {"online", "virtual", "remote"}
    CLASSROOM_WORDS = {"classroom", "offline", "in person", "in-person"}

    def __init__(self) -> None:
        pass

    def build_context(self, conversation, extracted_lead=None) -> LeadContext:
        context = LeadContext()
        self._apply_extracted_lead(context, extracted_lead)
        messages = self._normalize_messages(conversation)
        if not messages:
            return context

        previous_assistant_message = None
        for item in messages:
            role = item["role"]
            content = item["content"]
            if role == "user":
                if self.detect_lead_intent(content):
                    context.is_lead = True
                    # Lead intent is not automatically the interest.
                    # Example: "I am interested in joining your services"
                    # should still ask which actual product/service is wanted.
                    detected_interest = self.extract_interest_from_intent(content)
                    if detected_interest and not context.interest:
                        context.interest = detected_interest
                self._extract_explicit_information(context, content)
                if previous_assistant_message:
                    self._apply_answer_to_requested_field(
                        context,
                        previous_assistant_message,
                        content,
                    )
            elif role == "assistant":
                previous_assistant_message = content

        if self._conversation_contains_lead_data(context):
            context.is_lead = True
        return context

    def _apply_extracted_lead(self, context: LeadContext, extracted_lead) -> None:
        if extracted_lead is None:
            return
        for field in (
            "name", "phone", "email", "interest", "preferred_mode",
            "preferred_time", "notes",
        ):
            value = self._clean(getattr(extracted_lead, field, None))
            if value:
                setattr(context, field, value)
        if self._conversation_contains_lead_data(context):
            context.is_lead = True

    def _extract_explicit_information(self, context: LeadContext, message: str) -> None:
        name = self.extract_name(message)
        if name:
            context.name = name
        phone = self.extract_phone(message)
        if phone:
            context.phone = phone
        email = self.extract_email(message)
        if email:
            context.email = email
        preferred_mode = self.extract_preferred_mode(message)
        if preferred_mode:
            context.preferred_mode = preferred_mode
        preferred_time = self.extract_preferred_time(message)
        if preferred_time:
            context.preferred_time = preferred_time

    def _apply_answer_to_requested_field(self, context, assistant_message: str, user_message: str) -> None:
        field = self.get_requested_field(assistant_message)
        if not field:
            return
        if field == "name":
            value = self._extract_direct_name_answer(user_message)
            if value:
                context.name = value
        elif field == "phone":
            value = self.extract_phone(user_message)
            if value:
                context.phone = value
        elif field == "email":
            value = self.extract_email(user_message)
            if value:
                context.email = value
        elif field == "interest":
            value = (user_message or "").strip()
            if value:
                context.interest = value
        elif field == "preferred_mode":
            value = self.extract_preferred_mode(user_message)
            if value:
                context.preferred_mode = value
        elif field == "preferred_time":
            value = self.extract_preferred_time(user_message)
            if value:
                context.preferred_time = value

    @staticmethod
    def get_requested_field(assistant_message: str) -> str | None:
        text = (assistant_message or "").strip().lower()
        if not text:
            return None
        if "email address" in text or "email id" in text or any(
            marker in text for marker in ("share your email", "provide your email", "enter your email", "give your email")
        ):
            return "email"
        if "phone number" in text or "mobile number" in text or "contact number" in text or any(
            marker in text for marker in ("share your phone", "provide your phone", "enter your phone", "give your phone")
        ):
            return "phone"
        if "your name" in text or any(
            marker in text for marker in ("may i know your name", "could i know your name", "can i know your name")
        ):
            return "name"
        if any(marker in text for marker in (
            "what are you interested in", "which product", "which service",
            "what product", "what service", "what would you like to",
        )):
            return "interest"
        if "online or classroom" in text or "online or offline" in text or "preferred mode" in text:
            return "preferred_mode"
        if "preferred time" in text or "preferred timing" in text or "what time" in text:
            return "preferred_time"
        return None

    @classmethod
    def _is_lead_collection_question(cls, message: str) -> bool:
        return cls.get_requested_field(message) is not None

    def _extract_direct_name_answer(self, message: str) -> str | None:
        message = (message or "").strip()
        if not message:
            return None
        explicit = self.extract_name(message)
        if explicit:
            return explicit
        candidate = message.strip().strip(".").strip()
        if not candidate or "@" in candidate or any(c.isdigit() for c in candidate) or len(candidate) > 80:
            return None
        words = candidate.split()
        if not 1 <= len(words) <= 5:
            return None
        for word in words:
            if not re.fullmatch(r"[A-Za-z][A-Za-z.'-]*", word):
                return None
        if all(len(word) >= 5 and not re.search(r"[aeiou]", word, flags=re.IGNORECASE) for word in words):
            return None
        return candidate

    @staticmethod
    def _conversation_contains_lead_data(context: LeadContext) -> bool:
        return any((
            context.name, context.phone, context.email, context.interest,
            context.preferred_mode, context.preferred_time, context.notes,
        ))

    def detect_lead_intent(self, text: str) -> bool:
        normalized = self._normalize(text)
        return bool(normalized) and any(phrase in normalized for phrase in self.LEAD_INTENT_PHRASES)

    def extract_interest_from_intent(self, text: str) -> str | None:
        normalized = self._normalize(text)
        if not normalized:
            return None

        patterns = (
            r"\binterested\s+in\s+(?:the\s+)?(.+)$",
            r"\bwant\s+to\s+(?:join|enroll|register)\s+(?:for\s+)?(.+)$",
            r"\bwant\s+(?:to\s+)?(?:buy|purchase|book)\s+(.+)$",
        )
        for pattern in patterns:
            match = re.search(pattern, normalized, flags=re.IGNORECASE)
            if not match:
                continue
            value = match.group(1).strip(" .,!?:;")
            if not value:
                continue
            generic_values = {
                "your services", "your service", "services", "a service",
                "the services", "joining your services", "your courses",
            }
            if value in generic_values:
                return None
            if value.startswith(("joining your", "enrolling in your", "registering for your")):
                return None
            return value
        return None

    def extract_name(self, text: str) -> str | None:
        for index, pattern in enumerate(self.NAME_PATTERNS):
            match = re.search(pattern, text or "", flags=re.IGNORECASE)
            if not match:
                continue
            value = re.sub(r"\s+", " ", match.group(1).strip())
            value = re.split(r"[.!?,;:]", value, maxsplit=1)[0].strip()
            if index in {1, 2, 3}:
                first_word = value.split()[0].lower() if value else ""
                if first_word in self.NON_NAME_PREFIXES:
                    continue
            if self._looks_like_name(value):
                return value
        return None

    def extract_phone(self, text: str) -> str | None:
        if not text:
            return None
        compact = re.sub(r"[\s-]", "", text.strip())
        if compact.isdigit() and len(compact) > 10:
            return None
        match = self.PHONE_PATTERN.search(text)
        if not match:
            return None
        value = re.sub(r"[^\d+]", "", match.group(0))
        digits = value[3:] if value.startswith("+91") else value
        return value if len(digits) == 10 else None

    def extract_email(self, text: str) -> str | None:
        if not text:
            return None
        match = self.EMAIL_PATTERN.search(text)
        return match.group(0).lower().strip() if match else None

    def extract_preferred_mode(self, text: str) -> str | None:
        normalized = self._normalize(text)
        if not normalized:
            return None
        if any(value in normalized for value in self.ONLINE_WORDS):
            return "online"
        if any(value in normalized for value in self.CLASSROOM_WORDS):
            return "classroom"
        return None

    def extract_preferred_time(self, text: str) -> str | None:
        if not text:
            return None
        patterns = (
            r"\b\d{1,2}(?::\d{2})?\s*(?:am|pm)\b",
            r"\b\d{1,2}(?::\d{2})?\s*(?:a\.m\.|p\.m\.)\b",
        )
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                return match.group(0).strip()
        normalized = self._normalize(text)
        for value in ("morning", "afternoon", "evening", "night"):
            if value in normalized:
                return value
        return None

    def get_next_missing_field(self, context: LeadContext) -> str | None:
        if not context.interest:
            return "interest"
        if not context.name:
            return "name"
        if not context.phone:
            return "phone"
        if not context.email:
            return "email"
        return None

    def get_next_question(self, context: LeadContext) -> str | None:
        field = self.get_next_missing_field(context)
        if field == "interest":
            return "Sure! What product or service are you interested in?"
        if field == "name":
            return "Sure! May I know your name?"
        if field == "phone":
            return f"Thanks, {context.name}! Could you share your phone number?" if context.name else "Sure! Could you share your phone number?"
        if field == "email":
            return "Thanks! Could you share your email address?"
        return None

    def get_invalid_field_response(self, field: str | None, value: str) -> str | None:
        if field == "email":
            return "Please enter a valid email address, such as name@example.com." if value.strip() else "Could you share your email address?"
        if field == "phone":
            return "Please enter a valid phone number." if value.strip() else "Could you share your phone number?"
        if field == "name":
            return "Sorry, I didn't catch your name. Could you please provide it?" if value.strip() else "May I know your name?"
        if field == "interest":
            return "Which product or service would you like to enquire about?"
        return None

    def validate_field_answer(self, field: str | None, message: str) -> tuple[bool, str | None]:
        message = (message or "").strip()
        if not message:
            return False, None
        if field == "email":
            value = self.extract_email(message)
            return (True, value) if value else (False, None)
        if field == "phone":
            value = self.extract_phone(message)
            return (True, value) if value else (False, None)
        if field == "name":
            value = self._extract_direct_name_answer(message)
            return (True, value) if value else (False, None)
        if field == "interest":
            return True, message
        if field == "preferred_mode":
            value = self.extract_preferred_mode(message)
            return (True, value) if value else (False, None)
        if field == "preferred_time":
            value = self.extract_preferred_time(message)
            return (True, value) if value else (False, None)
        return False, None

    @staticmethod
    def _normalize(text: str) -> str:
        return " ".join((text or "").strip().lower().split())

    @staticmethod
    def _normalize_messages(messages) -> list[dict[str, str]]:
        if not messages:
            return []
        result = []
        for message in list(messages):
            role = getattr(message, "role", None)
            content = getattr(message, "content", None)
            if isinstance(message, dict):
                role = message.get("role")
                content = message.get("content")
            if not role or not content:
                continue
            role = str(role).strip().lower()
            content = str(content).strip()
            if role not in {"user", "assistant"} or not content:
                continue
            result.append({"role": role, "content": content})
        return result

    @staticmethod
    def _clean(value) -> str | None:
        if value is None:
            return None
        value = str(value).strip()
        return value or None

    @staticmethod
    def _looks_like_name(value: str) -> bool:
        if not value:
            return False
        words = value.split()
        if not 1 <= len(words) <= 5:
            return False
        return all(re.fullmatch(r"[A-Za-z][A-Za-z.'-]*", word) for word in words) and not all(
            len(word) >= 5 and not re.search(r"[aeiou]", word, flags=re.IGNORECASE)
            for word in words
        )
