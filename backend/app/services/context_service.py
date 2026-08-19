"""
Generic conversational context service.

Responsibilities:

- Detect explicit subjects
- Detect follow-up questions
- Detect company-wide questions
- Detect confirmations
- Preserve conversational subject
- Detect user intent
- Detect response length
- Build focused retrieval queries
- Detect general/unrelated questions
- Detect obvious gibberish
- Handle multiple questions
- Normalize conversation messages

This service is completely company-agnostic.

IMPORTANT:

This file contains NO company-specific subjects.

It does not know about:

- Python
- Java
- C
- Web Development
- Maruthi Technologies
- Any particular company's products/services

Subjects come from the customer's message and the
conversation context.

The knowledge base remains responsible for determining
whether a requested subject actually exists.
"""


import re


class ContextService:
    """
    Generic conversation understanding service.

    Processing priority:

    1. Empty / gibberish
    2. Negative confirmation
    3. Confirmation
    4. General conversation
    5. Company-wide request
    6. Explicit subject
    7. Follow-up
    8. General / unclear

    The service separates:

        SUBJECT
        INTENT
        MESSAGE TYPE
        RESPONSE STYLE

    Example:

        "How much fee for Python?"

    becomes approximately:

        subject = "python"
        intent = "fee"
        message_type = "new_topic"
        response_style = "short"
    """

    # =========================================================
    # SETTINGS
    # =========================================================

    DEFAULT_MESSAGE_LIMIT = 12

    MAX_CONTEXT_MESSAGES = 8

    MAX_MESSAGE_LENGTH = 1500

    MAX_SUBJECT_TERMS = 6

    MAX_RETRIEVAL_QUERY_LENGTH = 500

    # =========================================================
    # CONFIRMATIONS
    # =========================================================

    CONFIRMATION_WORDS = {
        "yes",
        "yeah",
        "yep",
        "yup",
        "sure",
        "okay",
        "ok",
        "alright",
        "fine",
        "please",
        "go ahead",
        "tell me",
        "yes please",
        "sure please",
        "okay please",
        "yes tell me",
        "yes please tell me",
    }

    NEGATIVE_CONFIRMATION_WORDS = {
        "no",
        "nope",
        "nah",
        "not now",
        "no thanks",
        "no thank you",
        "not interested",
    }

    # =========================================================
    # FOLLOW-UP WORDS
    # =========================================================

    FOLLOW_UP_WORDS = {
        "how",
        "much",
        "many",
        "what",
        "which",
        "where",
        "when",
        "why",

        "details",
        "detail",

        "information",
        "info",

        "topic",
        "topics",

        "covered",
        "cover",
        "covers",

        "syllabus",

        "fee",
        "fees",

        "price",
        "pricing",

        "cost",
        "costs",

        "duration",

        "time",
        "timing",
        "timings",

        "online",
        "offline",
        "classroom",

        "mode",

        "requirements",
        "requirement",

        "eligibility",

        "schedule",

        "location",
        "address",

        "contact",
        "phone",
        "email",

        "admission",
        "admissions",

        "registration",

        "available",
        "availability",

        "more",
        "please",

        "go",
        "ahead",

        "start",
        "started",

        "batch",

        "discount",
        "discounts",
        "reduce",
        "reduction",
    }

    # =========================================================
    # STOP WORDS
    # =========================================================

    STOP_WORDS = {
        "a",
        "an",
        "the",

        "is",
        "are",
        "am",
        "was",
        "were",
        "be",
        "been",
        "being",

        "do",
        "does",
        "did",

        "you",
        "your",
        "yours",
        "we",
        "our",
        "ours",

        "i",
        "me",
        "my",
        "mine",

        "he",
        "she",
        "they",
        "them",
        "their",

        "it",
        "its",

        "this",
        "that",
        "these",
        "those",

        "to",
        "of",
        "for",
        "from",
        "in",
        "on",
        "at",
        "by",
        "with",
        "about",
        "into",
        "over",
        "under",
        "through",

        "and",
        "or",
        "but",
        "if",
        "then",

        "can",
        "could",
        "would",
        "should",
        "will",
        "shall",
        "may",
        "might",

        "tell",
        "give",
        "provide",
        "show",
        "explain",

        "know",
        "want",
        "need",
        "like",
        "have",
        "has",
        "had",

        "what",
        "which",
        "who",
        "whom",
        "whose",
        "where",
        "when",
        "why",
        "how",

        "more",
        "some",
        "any",
        "all",
        "other",

        "details",
        "detail",
        "information",
        "info",

        "offer",
        "offers",
        "offered",

        "available",
        "availability",

        "course",
        "courses",
        "training",
        "class",
        "classes",
        "program",
        "programs",

        "service",
        "services",

        "product",
        "products",

        "yes",
        "yeah",
        "yep",
        "yup",
        "sure",

        "no",
        "nope",
        "nah",

        "okay",
        "ok",
        "alright",
        "fine",

        "please",

        "actually",
        "also",
        "just",
        "really",
        "very",

        "there",
        "here",

        "today",
        "tomorrow",
        "yesterday",

        "your",
        "company",
        "companies",

        "our",
        "business",

        "language",
        "technology",
    }

    # =========================================================
    # GENERAL CONVERSATION
    # =========================================================

    GENERAL_TOPIC_WORDS = {
        "weather",
        "recipe",
        "recipes",
        "joke",
        "cricket",
        "football",
        "soccer",
        "movie",
        "movies",
        "song",
        "songs",
        "news",
    }

    GENERAL_PHRASES = {
        "hello",
        "hi",
        "hey",

        "thanks",
        "thank you",

        "bye",
        "goodbye",

        "what is your name",
        "whats your name",

        "who are you",

        "what can you do",

        "how can you help me",
        "how can you help",
    }

    # =========================================================
    # COMPANY-WIDE QUESTIONS
    # =========================================================

    COMPANY_WIDE_PHRASES = {
        "what courses do you offer",
        "which courses do you offer",
        "what services do you offer",
        "which services do you offer",
        "what products do you offer",
        "which products do you offer",
        "what do you offer",
        "what does your company offer",
        "what are your services",
        "what are your products",
        "what are your courses",
        "what courses are available",
        "which courses are available",
        "what training do you offer",
        "which training do you offer",
        "what programs do you offer",
        "which programs do you offer",
    }

    # =========================================================
    # INTENT KEYWORDS
    # =========================================================

    FEE_PHRASES = {
        "how much",
        "how much fee",
        "how much does",
        "what is the fee",
        "what are the fees",
        "fee details",
        "fees",
        "fee",
        "price",
        "pricing",
        "cost",
        "costs",
        "tuition",
    }

    DISCOUNT_PHRASES = {
        "discount",
        "discounts",
        "reduce the fee",
        "reduce fee",
        "fee reduction",
        "concession",
    }

    TOPIC_PHRASES = {
        "what topics",
        "what topic",
        "topics covered",
        "topics",
        "syllabus",
        "what does it cover",
        "what is covered",
        "what are covered",
        "course content",
        "content",
    }

    DURATION_PHRASES = {
        "how long",
        "duration",
        "how many months",
        "how many days",
        "length of the course",
        "course duration",
    }

    TIMING_PHRASES = {
        "timing",
        "timings",
        "time",
        "schedule",
        "batch timing",
        "batch timings",
        "class timing",
        "class timings",
        "when is the class",
        "when are the classes",
    }

    AVAILABILITY_PHRASES = {
        "do you offer",
        "do you have",
        "is it available",
        "are you offering",
        "available",
        "availability",
        "offer",
        "offers",
    }

    MODE_PHRASES = {
        "online",
        "offline",
        "classroom",
        "mode",
        "online or classroom",
        "online and classroom",
    }

    ADMISSION_PHRASES = {
        "admission",
        "admissions",
        "registration",
        "enrollment",
        "enrolment",
        "when can i join",
        "when can i register",
        "when does it start",
        "when is the batch",
        "batch starts",
        "batch started",
        "started",
    }

    CONTACT_PHRASES = {
        "contact",
        "phone",
        "mobile",
        "email",
        "address",
        "location",
        "reach you",
        "contact details",
    }

    COMPANY_INFO_PHRASES = {
        "company name",
        "your name",
        "what is your company",
        "what's your company",
        "who are you",
        "about your company",
    }

    FULL_DETAILS_PHRASES = {
        "complete details",
        "full details",
        "all details",
        "everything about",
        "tell me everything",
        "complete information",
        "full information",
        "all information",
        "give me complete",
        "give me full details",
    }

    # =========================================================
    # INTENT LABELS
    # =========================================================

    INTENT_GENERAL = "general"

    INTENT_AVAILABILITY = "availability"

    INTENT_FEE = "fee"

    INTENT_DISCOUNT = "discount"

    INTENT_TOPICS = "topics"

    INTENT_DURATION = "duration"

    INTENT_TIMINGS = "timings"

    INTENT_DURATION_AND_TIMINGS = (
        "duration_and_timings"
    )

    INTENT_MODE = "mode"

    INTENT_ADMISSION = "admission"

    INTENT_CONTACT = "contact"

    INTENT_COMPANY_INFO = "company_information"

    INTENT_COMPANY_COURSES = "company_courses"

    INTENT_DETAILS = "details"

    INTENT_CONFIRMATION = "confirmation"

    INTENT_UNKNOWN = "unknown"

    # =========================================================
    # RESPONSE STYLES
    # =========================================================

    RESPONSE_SHORT = "short"

    RESPONSE_MEDIUM = "medium"

    RESPONSE_LONG = "long"

    # =========================================================
    # CONSTRUCTOR
    # =========================================================

    def __init__(
        self,
        message_limit: int = DEFAULT_MESSAGE_LIMIT,
    ) -> None:

        self.message_limit = max(
            1,
            message_limit,
        )

    # =========================================================
    # CLASSIFY MESSAGE
    # =========================================================

    def classify_message(
        self,
        message: str,
    ) -> str:
        """
        Classify the current customer message.

        Possible values:

            new_topic
            company_general
            follow_up
            confirmation
            negative_confirmation
            general
            unclear
        """

        message = (
            message or ""
        ).strip()

        if not message:

            return "unclear"

        normalized = (
            self._normalize_text(
                message
            )
        )

        if not normalized:

            return "unclear"

        # -----------------------------------------------------
        # 1. GIBBERISH
        # -----------------------------------------------------

        if self._looks_like_gibberish(
            message
        ):

            return "unclear"

        # -----------------------------------------------------
        # 2. NEGATIVE CONFIRMATION
        # -----------------------------------------------------

        if self.is_negative_confirmation(
            message
        ):

            return "negative_confirmation"

        # -----------------------------------------------------
        # 3. CONFIRMATION
        # -----------------------------------------------------

        if self.is_confirmation(
            message
        ):

            return "confirmation"

        # -----------------------------------------------------
        # 4. COMPANY INFORMATION
        #
        # This must be checked before general conversation:
        # "What's your company name?" needs verified knowledge,
        # not a generic assistant response.
        # -----------------------------------------------------

        if self._contains_any_phrase(
            message,
            self.COMPANY_INFO_PHRASES,
        ):

            return "company_general"

        # -----------------------------------------------------
        # 5. GENERAL CONVERSATION
        #
        # Must happen before subject extraction because:
        #
        # "What's your name?"
        #
        # should NOT become:
        #
        # subject = name
        # -----------------------------------------------------

        if self._is_general_question(
            message
        ):

            return "general"

        # -----------------------------------------------------
        # 6. COMPANY-WIDE QUESTION
        #
        # Must happen BEFORE subject extraction.
        #
        # Otherwise:
        #
        # "Which courses does your company offer?"
        #
        # can accidentally produce:
        #
        # subject = company
        # -----------------------------------------------------

        if self._is_company_wide_question(
            message
        ):

            return "company_general"

        # -----------------------------------------------------
        # 7. EXPLICIT SUBJECT
        # -----------------------------------------------------

        subject_terms = (
            self._extract_subject_terms(
                message
            )
        )

        if subject_terms:

            return "new_topic"

        # -----------------------------------------------------
        # 8. FOLLOW-UP
        # -----------------------------------------------------

        if self._looks_like_follow_up(
            message
        ):

            return "follow_up"

        # -----------------------------------------------------
        # 9. VERY SHORT INPUT
        # -----------------------------------------------------

        if len(
            normalized.split()
        ) <= 3:

            return "follow_up"

        # -----------------------------------------------------
        # 10. DEFAULT
        # -----------------------------------------------------

        return "general"

    # =========================================================
    # ANALYZE MESSAGE
    # =========================================================

    def analyze_message(
        self,
        message: str,
        messages=None,
    ) -> dict:
        """
        Produce a structured understanding of the current
        customer message.

        Example:

            {
                "message_type": "follow_up",
                "subject": "python",
                "intent": "fee",
                "response_style": "short",
                "requires_knowledge": True,
                "question_count": 1,
                "is_confirmation": False,
                "is_negative_confirmation": False,
                "retrieval_query": (
                    "CURRENT SUBJECT: python..."
                ),
            }

        This is the main method ChatService should use.
        """

        message = (
            message or ""
        ).strip()

        previous_messages = (
            messages or []
        )

        message_type = (
            self.classify_message(
                message
            )
        )

        previous_subject = (
            self.get_current_subject(
                previous_messages
            )
        )

        explicit_subject = (
            self.extract_subject(
                message
            )
        )

        # -----------------------------------------------------
        # Determine current subject
        # -----------------------------------------------------

        if explicit_subject:

            subject = explicit_subject

        elif message_type in {
            "follow_up",
            "confirmation",
        }:

            subject = previous_subject

        else:

            subject = None

        # -----------------------------------------------------
        # Intent
        # -----------------------------------------------------

        intent = (
            self.detect_intent(
                message
            )
        )

        # -----------------------------------------------------
        # Response style
        # -----------------------------------------------------

        response_style = (
            self.detect_response_style(
                message=message,
                intent=intent,
                question_count=self.count_questions(
                    message
                ),
            )
        )

        # -----------------------------------------------------
        # Knowledge requirement
        # -----------------------------------------------------

        requires_knowledge = (
            self.requires_knowledge(
                message_type=message_type,
                intent=intent,
            )
        )

        # -----------------------------------------------------
        # Retrieval query
        # -----------------------------------------------------

        retrieval_query = (
            self.build_retrieval_query(
                current_message=message,
                messages=previous_messages,
            )
        )

        return {
            "message_type": message_type,
            "subject": subject,
            "explicit_subject": explicit_subject,
            "previous_subject": previous_subject,
            "intent": intent,
            "response_style": response_style,
            "requires_knowledge": (
                requires_knowledge
            ),
            "question_count": (
                self.count_questions(
                    message
                )
            ),
            "is_confirmation": (
                message_type
                == "confirmation"
            ),
            "is_negative_confirmation": (
                message_type
                == "negative_confirmation"
            ),
            "retrieval_query": retrieval_query,
        }

    # =========================================================
    # INTENT DETECTION
    # =========================================================

    def detect_intent(
        self,
        message: str,
    ) -> str:
        """
        Detect what the customer wants to know.

        IMPORTANT:

        Intent is separate from subject.

        Example:

            "How much is Python?"

        subject = python
        intent = fee
        """

        normalized = (
            self._normalize_text(
                message
            )
        )

        if not normalized:

            return self.INTENT_UNKNOWN

        # -----------------------------------------------------
        # Company identity
        # -----------------------------------------------------

        if self._contains_any_phrase(
            normalized,
            self.COMPANY_INFO_PHRASES,
        ):

            return self.INTENT_COMPANY_INFO

        # -----------------------------------------------------
        # Complete details
        # -----------------------------------------------------

        if self._contains_any_phrase(
            normalized,
            self.FULL_DETAILS_PHRASES,
        ):

            return self.INTENT_DETAILS

        # -----------------------------------------------------
        # Multiple specific requests
        # -----------------------------------------------------

        has_duration = (
            self._contains_any_phrase(
                normalized,
                self.DURATION_PHRASES,
            )
        )

        has_timings = (
            self._contains_any_phrase(
                normalized,
                self.TIMING_PHRASES,
            )
        )

        if (
            has_duration
            and has_timings
        ):

            return self.INTENT_DURATION_AND_TIMINGS

        # -----------------------------------------------------
        # Discount / concession
        # -----------------------------------------------------

        if self._contains_any_phrase(
            normalized,
            self.DISCOUNT_PHRASES,
        ):

            return self.INTENT_DISCOUNT

        # -----------------------------------------------------
        # Fee
        # -----------------------------------------------------

        if self._contains_any_phrase(
            normalized,
            self.FEE_PHRASES,
        ):

            return self.INTENT_FEE

        # -----------------------------------------------------
        # Topics
        # -----------------------------------------------------

        if self._contains_any_phrase(
            normalized,
            self.TOPIC_PHRASES,
        ):

            return self.INTENT_TOPICS

        # -----------------------------------------------------
        # Duration
        # -----------------------------------------------------

        if has_duration:

            return self.INTENT_DURATION

        # -----------------------------------------------------
        # Timings
        # -----------------------------------------------------

        if has_timings:

            return self.INTENT_TIMINGS

        # -----------------------------------------------------
        # Admission / batch
        # -----------------------------------------------------

        if self._contains_any_phrase(
            normalized,
            self.ADMISSION_PHRASES,
        ):

            return self.INTENT_ADMISSION

        # -----------------------------------------------------
        # Mode
        # -----------------------------------------------------

        if self._contains_any_phrase(
            normalized,
            self.MODE_PHRASES,
        ):

            return self.INTENT_MODE

        # -----------------------------------------------------
        # Contact
        # -----------------------------------------------------

        if self._contains_any_phrase(
            normalized,
            self.CONTACT_PHRASES,
        ):

            return self.INTENT_CONTACT

        # -----------------------------------------------------
        # Company courses
        # -----------------------------------------------------

        if self._is_company_wide_question(
            normalized
        ):

            return self.INTENT_COMPANY_COURSES

        # -----------------------------------------------------
        # Availability
        # -----------------------------------------------------

        if self._contains_any_phrase(
            normalized,
            self.AVAILABILITY_PHRASES,
        ):

            return self.INTENT_AVAILABILITY

        # -----------------------------------------------------
        # Confirmation
        # -----------------------------------------------------

        if self.is_confirmation(
            normalized
        ):

            return self.INTENT_CONFIRMATION

        return self.INTENT_GENERAL

    # =========================================================
    # RESPONSE STYLE
    # =========================================================

    def detect_response_style(
        self,
        message: str,
        intent: str | None = None,
        question_count: int | None = None,
    ) -> str:
        """
        Decide how much information the AI should provide.

        SHORT:

            "How much?"
            "Do you offer Python?"
            "What's the fee?"

        MEDIUM:

            "What topics are covered?"
            "Tell me about Python."
            "What are the duration and timings?"

        LONG:

            "Give me complete details about Python."
            "Tell me everything about the course."
        """

        normalized = (
            self._normalize_text(
                message
            )
        )

        if not normalized:

            return self.RESPONSE_SHORT

        if question_count is None:

            question_count = (
                self.count_questions(
                    message
                )
            )

        # -----------------------------------------------------
        # Explicit request for complete information
        # -----------------------------------------------------

        if self._contains_any_phrase(
            normalized,
            self.FULL_DETAILS_PHRASES,
        ):

            return self.RESPONSE_LONG

        # -----------------------------------------------------
        # Multiple questions
        # -----------------------------------------------------

        if question_count >= 3:

            return self.RESPONSE_LONG

        if question_count == 2:

            return self.RESPONSE_MEDIUM

        # -----------------------------------------------------
        # Broad details
        # -----------------------------------------------------

        broad_detail_phrases = {
            "tell me about",
            "tell me more about",
            "explain the course",
            "explain everything",
            "course details",
            "details about",
            "more information about",
            "give me information",
        }

        if self._contains_any_phrase(
            normalized,
            broad_detail_phrases,
        ):

            return self.RESPONSE_MEDIUM

        # -----------------------------------------------------
        # Topic lists
        # -----------------------------------------------------

        if intent in {
            self.INTENT_TOPICS,
            self.INTENT_DURATION_AND_TIMINGS,
            self.INTENT_DETAILS,
        }:

            return self.RESPONSE_MEDIUM

        # -----------------------------------------------------
        # Company-wide requests
        # -----------------------------------------------------

        if intent in {
            self.INTENT_COMPANY_COURSES,
        }:

            return self.RESPONSE_MEDIUM

        # -----------------------------------------------------
        # Default
        # -----------------------------------------------------

        return self.RESPONSE_SHORT

    # =========================================================
    # KNOWLEDGE REQUIREMENT
    # =========================================================

    @staticmethod
    def requires_knowledge(
        message_type: str,
        intent: str,
    ) -> bool:
        """
        Determine whether verified company knowledge is
        required.

        Generic greetings and casual conversation do not
        require retrieval.

        Company/course/product/service questions do.
        """

        if message_type in {
            "unclear",
            "general",
            "confirmation",
            "negative_confirmation",
        }:

            return False

        # An explicit topic or follow-up is a company-information
        # request even when it has no narrowly classified intent.
        # Examples: "I want to learn Java" and "What about it?"
        # must use verified knowledge rather than let the LLM guess.
        if message_type in {
            "new_topic",
            "follow_up",
            "company_general",
        }:

            return True

        if intent in {
            ContextService.INTENT_GENERAL,
            ContextService.INTENT_CONFIRMATION,
        }:

            return False

        return True

    # =========================================================
    # EXPLICIT SUBJECT
    # =========================================================

    def extract_subject(
        self,
        message: str,
    ) -> str | None:
        """
        Return a clean subject string.

        Examples:

            "Do you offer Python?"
                -> "python"

            "How much fee for Python?"
                -> "python"

            "What about Java?"
                -> "java"

            "What are the timings for C language?"
                -> "c language"

            "How much?"
                -> None
        """

        terms = (
            self._extract_subject_terms(
                message
            )
        )

        if not terms:

            return None

        return " ".join(
            terms[
                :self.MAX_SUBJECT_TERMS
            ]
        )

    # =========================================================
    # COMPANY-WIDE QUESTION
    # =========================================================

    def _is_company_wide_question(
        self,
        message: str,
    ) -> bool:

        normalized = (
            self._normalize_text(
                message
            )
        )

        if not normalized:

            return False

        if normalized in self.COMPANY_WIDE_PHRASES:

            return True

        patterns = (
            r"^what (courses|services|products) "
            r"do you offer$",

            r"^which (courses|services|products) "
            r"do you offer$",

            r"^what do you offer$",

            r"^what are your "
            r"(courses|services|products)$",

            r"^(what|which) courses "
            r"(does|do) (your|the) company offer$",

            r"^(what|which) courses "
            r"are (you|your company) offering$",

            r"^(what|which) services "
            r"(does|do) (your|the) company offer$",

            r"^what does your company offer$",

            r"^what are you offering$",
        )

        if any(
            re.search(
                pattern,
                normalized,
            )
            for pattern in patterns
        ):

            return True

        # -----------------------------------------------------
        # Flexible company-wide detection.
        #
        # This catches:
        #
        # "Which courses your company offers?"
        #
        # "What courses does your company offer?"
        #
        # "What courses are offered?"
        # -----------------------------------------------------

        has_course_word = any(
            word in normalized
            for word in (
                "course",
                "courses",
                "training",
                "program",
                "programs",
            )
        )

        has_offer_word = any(
            phrase in normalized
            for phrase in (
                "offer",
                "offers",
                "offering",
                "provide",
                "provides",
                "available",
            )
        )

        has_company_reference = any(
            phrase in normalized
            for phrase in (
                "your company",
                "your business",
                "your organization",
                "company",
                "business",
            )
        )

        if (
            has_course_word
            and has_offer_word
            and (
                has_company_reference
                or normalized.startswith(
                    (
                        "what courses",
                        "which courses",
                        "what training",
                        "which training",
                    )
                )
            )
        ):

            return True

        return False

    # =========================================================
    # FOLLOW-UP DETECTION
    # =========================================================

    def _looks_like_follow_up(
        self,
        message: str,
    ) -> bool:
        """
        Detect questions about an already-known subject.

        IMPORTANT:

        This method should NOT decide the subject.

        It only determines whether the message looks like
        a continuation of the previous conversation.
        """

        normalized = (
            self._normalize_text(
                message
            )
        )

        if not normalized:

            return False

        # -----------------------------------------------------
        # Strong follow-up phrases
        # -----------------------------------------------------

        strong_phrases = (
            "how much",
            "how many",
            "what topics",
            "what topic",
            "topics covered",
            "what is the fee",
            "what are the fees",
            "what is the price",
            "what is the cost",
            "how long",
            "what is the duration",
            "what are the timings",
            "what is the timing",
            "what is the schedule",
            "what are the timings",
            "tell me more",
            "give me details",
            "provide details",
            "more details",
            "more information",
            "what about it",
            "what about that",
            "and how much",
            "and what topics",
            "and what about",
        )

        if any(
            phrase in normalized
            for phrase in strong_phrases
        ):

            return True

        # -----------------------------------------------------
        # Typo-tolerant intent words
        #
        # This specifically prevents things such as:
        #
        # "timimgs"
        # "timngs"
        # "topcs"
        #
        # from becoming the subject.
        # -----------------------------------------------------

        if self._contains_fuzzy_intent_word(
            normalized
        ):

            if not self._extract_subject_terms(
                message
            ):

                return True

        words = set(
            re.findall(
                r"[A-Za-z0-9+#.-]+",
                normalized,
            )
        )

        if (
            words
            & self.FOLLOW_UP_WORDS
        ):

            if not self._extract_subject_terms(
                message
            ):

                return True

        return False

    # =========================================================
    # FUZZY INTENT WORD DETECTION
    # =========================================================

    def _contains_fuzzy_intent_word(
        self,
        normalized: str,
    ) -> bool:
        """
        Detect common intent words even with small spelling
        mistakes.

        Examples:

            timings -> timimgs
            topics  -> topcs
            details -> detials
            duration -> duraton
        """

        words = re.findall(
            r"[a-zA-Z]+",
            normalized,
        )

        intent_words = (
            "timing",
            "timings",
            "topics",
            "topic",
            "details",
            "detail",
            "duration",
            "fees",
            "fee",
            "price",
            "pricing",
            "cost",
            "syllabus",
            "schedule",
            "admission",
            "availability",
            "available",
        )

        for word in words:

            for target in intent_words:

                if self._similarity_ratio(
                    word,
                    target,
                ) >= 0.78:

                    return True

        return False

    # =========================================================
    # SUBJECT
    # =========================================================

    def get_current_subject(
        self,
        messages,
    ) -> str | None:
        """
        Find the latest genuine subject introduced by the
        customer.

        Assistant messages are NEVER allowed to introduce
        a subject.
        """

        normalized = (
            self._normalize_messages(
                messages
            )
        )

        for index in range(
            len(normalized) - 1,
            -1,
            -1,
        ):

            item = normalized[index]

            if item["role"] != "user":

                continue

            content = item["content"]

            # A direct response to a lead-detail prompt is personal
            # data, never the topic of the conversation. Without this
            # guard, names and email addresses can become the subject
            # of later questions such as "What's the fee?".
            if (
                index > 0
                and normalized[index - 1]["role"] == "assistant"
                and self._is_lead_detail_question(
                    normalized[index - 1]["content"]
                )
            ):

                continue

            message_type = (
                self.classify_message(
                    content
                )
            )

            if message_type != "new_topic":

                continue

            subject = (
                self.extract_subject(
                    content
                )
            )

            if not subject:

                continue

            return subject

        return None

    @staticmethod
    def _is_lead_detail_question(
        message: str,
    ) -> bool:
        """Return whether an assistant message requests lead data."""

        text = " ".join(
            (message or "")
            .lower()
            .split()
        )

        return any(
            phrase in text
            for phrase in (
                "your name",
                "phone number",
                "mobile number",
                "contact number",
                "email address",
                "email id",
                "share your email",
                "share your phone",
            )
        )

    # =========================================================
    # RETRIEVAL QUERY
    # =========================================================

    def build_retrieval_query(
        self,
        current_message: str,
        messages,
    ) -> str:
        """
        Build a focused retrieval query.

        Follow-up example:

            Previous:
                Do you offer Python?

            Current:
                How much?

        Query becomes:

            CURRENT SUBJECT: python
            CUSTOMER INTENT: fee
            CUSTOMER QUESTION: How much?
        """

        current_message = (
            current_message or ""
        ).strip()

        if not current_message:

            return ""

        previous_messages = (
            self._normalize_messages(
                messages
            )
        )

        previous_messages = (
            self._remove_current_message(
                current_message,
                previous_messages,
            )
        )

        message_type = (
            self.classify_message(
                current_message
            )
        )

        intent = (
            self.detect_intent(
                current_message
            )
        )

        subject = (
            self.extract_subject(
                current_message
            )
        )

        # -----------------------------------------------------
        # NEW SUBJECT
        # -----------------------------------------------------

        if message_type == "new_topic":

            parts = []

            if subject:

                parts.append(
                    f"SUBJECT: {subject}"
                )

            parts.append(
                f"INTENT: {intent}"
            )

            parts.append(
                f"QUESTION: {current_message}"
            )

            return self._limit_query(
                "\n".join(parts)
            )

        # -----------------------------------------------------
        # COMPANY-WIDE
        # -----------------------------------------------------

        if message_type == "company_general":

            return self._limit_query(
                (
                    f"INTENT: {intent}\n"
                    f"COMPANY QUESTION: "
                    f"{current_message}"
                )
            )

        # -----------------------------------------------------
        # GENERAL
        # -----------------------------------------------------

        if message_type == "general":

            return ""

        # -----------------------------------------------------
        # UNCLEAR
        # -----------------------------------------------------

        if message_type == "unclear":

            return ""

        # -----------------------------------------------------
        # PREVIOUS SUBJECT
        # -----------------------------------------------------

        previous_subject = (
            self.get_current_subject(
                previous_messages
            )
        )

        # -----------------------------------------------------
        # CONFIRMATION
        # -----------------------------------------------------

        if message_type == "confirmation":

            pending_question = (
                self.get_pending_assistant_question(
                    previous_messages
                )
            )

            parts = []

            if previous_subject:

                parts.append(
                    f"CURRENT SUBJECT: "
                    f"{previous_subject}"
                )

            parts.append(
                f"INTENT: {intent}"
            )

            if pending_question:

                parts.append(
                    "PENDING ASSISTANT QUESTION: "
                    f"{pending_question}"
                )

            parts.append(
                f"CUSTOMER CONFIRMATION: "
                f"{current_message}"
            )

            return self._limit_query(
                "\n".join(parts)
            )

        # -----------------------------------------------------
        # FOLLOW-UP
        # -----------------------------------------------------

        if message_type == "follow_up":

            parts = []

            if previous_subject:

                parts.append(
                    f"CURRENT SUBJECT: "
                    f"{previous_subject}"
                )

            parts.append(
                f"INTENT: {intent}"
            )

            parts.append(
                f"CUSTOMER QUESTION: "
                f"{current_message}"
            )

            return self._limit_query(
                "\n".join(parts)
            )

        return self._limit_query(
            current_message
        )

    # =========================================================
    # PENDING ASSISTANT QUESTION
    # =========================================================

    def get_pending_assistant_question(
        self,
        messages,
    ) -> str | None:

        normalized = (
            self._normalize_messages(
                messages
            )
        )

        for item in reversed(
            normalized
        ):

            if item["role"] != "assistant":

                continue

            content = item["content"].strip()

            if not content:

                continue

            if self._looks_like_question(
                content
            ):

                return content

        return None

    # =========================================================
    # LAST USER
    # =========================================================

    def get_last_user_message(
        self,
        messages,
    ) -> str | None:

        normalized = (
            self._normalize_messages(
                messages
            )
        )

        for item in reversed(
            normalized
        ):

            if item["role"] == "user":

                return item["content"]

        return None

    # =========================================================
    # LAST ASSISTANT
    # =========================================================

    def get_last_assistant_message(
        self,
        messages,
    ) -> str | None:

        normalized = (
            self._normalize_messages(
                messages
            )
        )

        for item in reversed(
            normalized
        ):

            if item["role"] == "assistant":

                return item["content"]

        return None

    # =========================================================
    # CONFIRMATION
    # =========================================================

    def is_confirmation(
        self,
        message: str,
    ) -> bool:

        normalized = (
            self._normalize_text(
                message
            )
        )

        cleaned = re.sub(
            r"[^\w\s+#.-]",
            " ",
            normalized,
        )

        cleaned = " ".join(
            cleaned.split()
        )

        return (
            cleaned
            in self.CONFIRMATION_WORDS
        )

    # =========================================================
    # NEGATIVE CONFIRMATION
    # =========================================================

    def is_negative_confirmation(
        self,
        message: str,
    ) -> bool:

        normalized = (
            self._normalize_text(
                message
            )
        )

        cleaned = re.sub(
            r"[^\w\s+#.-]",
            " ",
            normalized,
        )

        cleaned = " ".join(
            cleaned.split()
        )

        return (
            cleaned
            in self.NEGATIVE_CONFIRMATION_WORDS
        )

    # =========================================================
    # GENERAL QUESTION
    # =========================================================

    def _is_general_question(
        self,
        message: str,
    ) -> bool:

        normalized = (
            self._normalize_text(
                message
            )
        )

        if not normalized:

            return True

        if normalized in self.GENERAL_PHRASES:

            return True

        words = set(
            re.findall(
                r"[A-Za-z0-9+#.-]+",
                normalized,
            )
        )

        if (
            words
            & self.GENERAL_TOPIC_WORDS
        ):

            return True

        if (
            "name" in words
            and (
                "your" in words
                or "you" in words
            )
        ):

            return True

        if (
            "who" in words
            and "you" in words
        ):

            return True

        return False

    # =========================================================
    # SUBJECT EXTRACTION
    # =========================================================

    def _extract_subject_terms(
        self,
        message: str,
    ) -> list[str]:
        """
        Extract likely subject terms.

        IMPORTANT:

        Intent words are removed from the subject.

        Therefore:

            "how much fee for python"

        becomes:

            ["python"]

        rather than:

            ["much", "fee", "python"]

        Also handles:

            C language
            C programming
            web technology
            machine learning
        """

        raw_message = (
            message or ""
        ).strip()

        # Contact details must never be interpreted as a product,
        # service, or course subject.
        if re.fullmatch(
            r"[A-Za-z0-9._%+-]+"
            r"@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
            raw_message,
        ):

            return []

        if re.fullmatch(
            r"\+?[\d\s-]{7,}",
            raw_message,
        ):

            return []

        normalized = (
            self._normalize_text(
                raw_message
            )
        )

        if not normalized:

            return []

        words = re.findall(
            r"[A-Za-z0-9+#.-]+",
            normalized,
        )

        terms = []

        generic_terms = {
            "what's",
            "whats",
            "name",
            "help",
            "hello",
            "hi",
            "hey",
            "thanks",
            "thank",
            "bye",
            "goodbye",

            "interested",
            "interest",
            "looking",

            "want",
            "need",
            "learn",
            "learning",
            "join",
            "joining",

            "provide",
            "provided",
            "provides",

            "explain",
            "explanation",

            "know",
            "knowing",

            "details",
            "detail",

            "information",
            "info",

            "company",
            "business",
            "organization",

            "batch",
            "started",
            "start",
            "admission",
            "admissions",
            "enrollment",
            "enrolment",
            "open",

            "language",
            "technology",
        }

        intent_terms = (
            self.FOLLOW_UP_WORDS
            | {
                "offer",
                "offers",
                "offering",
                "course",
                "courses",
                "training",
                "class",
                "classes",
                "program",
                "programs",
                "service",
                "services",
                "product",
                "products",
            }
        )

        for word in words:

            cleaned = word.strip(
                ".-"
            )

            if not cleaned:

                continue

            if cleaned in self.STOP_WORDS:

                continue

            if cleaned in intent_terms:

                continue

            if cleaned in generic_terms:

                continue

            # Ignore obvious keyboard-gibberish tokens while leaving
            # short abbreviations such as C, SQL, and HTML available.
            if (
                len(cleaned) >= 5
                and not re.search(
                    r"[aeiou]",
                    cleaned,
                    flags=re.IGNORECASE,
                )
            ):

                continue

            if (
                len(cleaned) <= 1
                and cleaned != "c"
            ):

                continue

            if cleaned not in terms:

                terms.append(
                    cleaned
                )

        return terms[
            :self.MAX_SUBJECT_TERMS
        ]

    # =========================================================
    # QUESTION COUNT
    # =========================================================

    @staticmethod
    def count_questions(
        message: str,
    ) -> int:
        """
        Estimate how many questions are in the message.

        Examples:

            "How much?"
                -> 1

            "What is the fee and duration?"
                -> 1

            "What is the fee? What are the timings?"
                -> 2

            "What courses do you offer? What's your name?"
                -> 2
        """

        message = (
            message or ""
        ).strip()

        if not message:

            return 0

        explicit_marks = (
            message.count("?")
        )

        if explicit_marks > 0:

            return explicit_marks

        normalized = (
            " ".join(
                message.lower().split()
            )
        )

        patterns = (
            r"\bwhat\b",
            r"\bhow\b",
            r"\bwhen\b",
            r"\bwhere\b",
            r"\bwhy\b",
            r"\bwhich\b",
            r"\bwho\b",
            r"\bdo you\b",
            r"\bdoes your\b",
            r"\bcan you\b",
            r"\bis there\b",
            r"\bare there\b",
        )

        count = sum(
            1
            for pattern in patterns
            if re.search(
                pattern,
                normalized,
            )
        )

        return max(
            1,
            min(
                count,
                5,
            ),
        )

    # =========================================================
    # QUESTION DETECTION
    # =========================================================

    @staticmethod
    def _looks_like_question(
        text: str,
    ) -> bool:

        text = (
            text or ""
        ).strip()

        if not text:

            return False

        if "?" in text:

            return True

        normalized = " ".join(
            text.lower().split()
        )

        patterns = (
            r"\bwould you like\b",
            r"\bdo you want\b",
            r"\bwould you prefer\b",
            r"\bcan i help\b",
            r"\bmay i\b",
            r"\bshall i\b",
            r"\bare you looking\b",
            r"\bwhich one\b",
            r"\bwhat would you like\b",
            r"\bwould you be interested\b",
        )

        return any(
            re.search(
                pattern,
                normalized,
            )
            for pattern in patterns
        )

    # =========================================================
    # GIBBERISH
    # =========================================================

    def _looks_like_gibberish(
        self,
        message: str,
    ) -> bool:

        stripped = (
            message.strip()
        )

        if not stripped:

            return True

        if not re.search(
            r"[A-Za-z0-9]",
            stripped,
        ):

            return True

        symbols = re.findall(
            r"[^A-Za-z0-9\s]",
            stripped,
        )

        total = len(
            stripped
        )

        if total >= 5:

            ratio = (
                len(symbols)
                / total
            )

            if ratio >= 0.70:

                return True

        # -----------------------------------------------------
        # Detect repeated random symbols.
        # -----------------------------------------------------

        if re.fullmatch(
            r"[\W_]{3,}",
            stripped,
        ):

            return True

        # A standalone long mix of letters and digits is usually an
        # accidental keystroke, not a question or a usable subject.
        # Product codes still work when they appear in a real query
        # such as "Do you offer ABC123?".
        compact = re.sub(
            r"\s+",
            "",
            stripped,
        )

        if (
            len(compact) >= 7
            and re.fullmatch(
                r"(?=.*[A-Za-z])(?=.*\d)[A-Za-z0-9]+",
                compact,
            )
        ):

            return True

        # A sequence of several letter-only tokens with no vowels is
        # overwhelmingly likely to be accidental keyboard input, not
        # a company subject. Keep short names and technical acronyms
        # valid by requiring at least three such tokens.
        letter_words = re.findall(
            r"[A-Za-z]+",
            stripped,
        )

        if (
            len(letter_words) >= 3
            and all(
                not re.search(
                    r"[aeiou]",
                    word,
                    flags=re.IGNORECASE,
                )
                for word in letter_words
            )
        ):

            return True

        return False

    # =========================================================
    # NORMALIZE TEXT
    # =========================================================

    @staticmethod
    def _normalize_text(
        text: str,
    ) -> str:

        text = (
            text or ""
        ).strip().lower()

        # Keep characters that occur in valid technical names (C++,
        # C#, Node.js, etc.), but treat sentence punctuation and
        # separators as whitespace. This makes question variants such
        # as "Which courses do you offer>" classify correctly.
        text = re.sub(
            r"[^a-z0-9+#.\-\s]",
            " ",
            text,
        )

        return " ".join(
            text.split()
        )

    # =========================================================
    # REMOVE CURRENT MESSAGE
    # =========================================================

    def _remove_current_message(
        self,
        current_message: str,
        messages,
    ) -> list:

        if not messages:

            return []

        result = list(
            messages
        )

        current_normalized = (
            self._normalize_text(
                current_message
            )
        )

        if not result:

            return []

        last = result[-1]

        role = getattr(
            last,
            "role",
            None,
        )

        content = getattr(
            last,
            "content",
            None,
        )

        if isinstance(
            last,
            dict,
        ):

            role = last.get(
                "role"
            )

            content = last.get(
                "content"
            )

        if (
            str(
                role or ""
            ).strip().lower()
            == "user"
            and self._normalize_text(
                str(
                    content or ""
                )
            )
            == current_normalized
        ):

            return result[:-1]

        return result

    # =========================================================
    # NORMALIZE MESSAGES
    # =========================================================

    def _normalize_messages(
        self,
        messages,
    ) -> list[dict[str, str]]:

        if not messages:

            return []

        result = []

        try:

            message_list = list(
                messages
            )[
                -self.message_limit:
            ]

        except TypeError:

            return []

        for message in message_list:

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

            if role is None:
                continue

            if content is None:
                continue

            role = str(
                role
            ).strip().lower()

            content = str(
                content
            ).strip()

            if not content:
                continue

            if role not in {
                "user",
                "assistant",
                "system",
            }:
                continue

            # -------------------------------------------------
            # IMPORTANT FIX:
            #
            # Always reference self.MAX_MESSAGE_LENGTH.
            #
            # Previously:
            #
            # content[:MAX_MESSAGE_LENGTH]
            #
            # caused:
            #
            # NameError:
            # MAX_MESSAGE_LENGTH is not defined
            # -------------------------------------------------

            if len(
                content
            ) > self.MAX_MESSAGE_LENGTH:

                content = (
                    content[
                        : self.MAX_MESSAGE_LENGTH
                    ]
                    + "..."
                )

            result.append(
                {
                    "role": role,
                    "content": content,
                }
            )

        return result

    # =========================================================
    # BUILD CONTEXT
    # =========================================================

    def build_context(
        self,
        messages,
    ) -> str:

        normalized = (
            self._normalize_messages(
                messages
            )
        )

        if not normalized:

            return (
                "No previous conversation."
            )

        recent = normalized[
            -self.MAX_CONTEXT_MESSAGES:
        ]

        return "\n".join(
            (
                f"{item['role'].upper()}: "
                f"{item['content']}"
            )
            for item in recent
        )

    # =========================================================
    # SIMILARITY RATIO
    # =========================================================

    @staticmethod
    def _similarity_ratio(
        first: str,
        second: str,
    ) -> float:
        """
        Lightweight character similarity.

        Used only for typo tolerance.

        No external package is required.
        """

        first = (
            first or ""
        ).lower()

        second = (
            second or ""
        ).lower()

        if not first or not second:

            return 0.0

        if first == second:

            return 1.0

        # -----------------------------------------------------
        # Simple dynamic-programming Levenshtein distance.
        # -----------------------------------------------------

        previous = list(
            range(
                len(second) + 1
            )
        )

        for i, char_a in enumerate(
            first,
            start=1,
        ):

            current = [
                i
            ]

            for j, char_b in enumerate(
                second,
                start=1,
            ):

                insert_cost = (
                    current[j - 1]
                    + 1
                )

                delete_cost = (
                    previous[j]
                    + 1
                )

                replace_cost = (
                    previous[j - 1]
                    + (
                        char_a
                        != char_b
                    )
                )

                current.append(
                    min(
                        insert_cost,
                        delete_cost,
                        replace_cost,
                    )
                )

            previous = current

        distance = previous[
            -1
        ]

        max_length = max(
            len(first),
            len(second),
        )

        if max_length == 0:

            return 1.0

        return (
            1.0
            - (
                distance
                / max_length
            )
        )

    # =========================================================
    # PHRASE MATCHING
    # =========================================================

    @staticmethod
    def _contains_any_phrase(
        text: str,
        phrases: set[str],
    ) -> bool:
        """
        Return True if any phrase occurs in the normalized
        text.
        """

        normalized = (
            text or ""
        ).strip().lower()
        if not normalized:

            return False

        for phrase in phrases:

            phrase = (
                phrase or ""
            ).strip().lower()

            if not phrase:

                continue

            if phrase in normalized:

                return True

        return False

    # =========================================================
    # QUERY LENGTH LIMIT
    # =========================================================

    def _limit_query(
        self,
        query: str,
    ) -> str:

        query = (
            query or ""
        ).strip()

        if len(
            query
        ) <= self.MAX_RETRIEVAL_QUERY_LENGTH:

            return query

        return (
            query[
                : self.MAX_RETRIEVAL_QUERY_LENGTH
            ]
            + "..."
        )
