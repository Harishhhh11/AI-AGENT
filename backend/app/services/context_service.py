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
"""

import re


class ContextService:
    DEFAULT_MESSAGE_LIMIT = 12
    MAX_CONTEXT_MESSAGES = 8
    MAX_MESSAGE_LENGTH = 1500
    MAX_SUBJECT_TERMS = 6
    MAX_RETRIEVAL_QUERY_LENGTH = 500

    CONFIRMATION_WORDS = {
        "yes", "yeah", "yep", "yup", "sure", "okay", "ok", "alright", "fine",
        "please", "go ahead", "tell me", "yes please", "sure please", "okay please",
        "yes tell me", "yes please tell me",
    }
    NEGATIVE_CONFIRMATION_WORDS = {"no", "nope", "nah", "not now", "no thanks", "no thank you", "not interested"}

    FOLLOW_UP_WORDS = {
        "how", "much", "many", "what", "which", "where", "when", "why", "details", "detail",
        "information", "info", "topic", "topics", "covered", "cover", "covers", "syllabus",
        "fee", "fees", "price", "pricing", "cost", "costs", "duration", "time", "timing", "timings",
        "online", "offline", "classroom", "mode", "requirements", "requirement", "eligibility", "schedule",
        "location", "address", "contact", "phone", "email", "admission", "admissions", "registration",
        "available", "availability", "more", "please", "go", "ahead", "start", "started", "batch",
        "discount", "discounts", "reduce", "reduction", "tell",
    }

    STOP_WORDS = {
        "a", "an", "the", "is", "are", "am", "was", "were", "be", "been", "being", "do", "does", "did",
        "you", "your", "yours", "we", "our", "ours", "i", "me", "my", "mine", "he", "she", "they", "them",
        "their", "it", "its", "this", "that", "these", "those", "to", "of", "for", "from", "in", "on", "at",
        "by", "with", "about", "into", "over", "under", "through", "and", "or", "but", "if", "then", "can",
        "could", "would", "should", "will", "shall", "may", "might", "tell", "give", "provide", "show", "explain",
        "know", "want", "need", "like", "have", "has", "had", "what", "which", "who", "whom", "whose", "where",
        "when", "why", "how", "more", "some", "any", "all", "other", "details", "detail", "information", "info",
        "offer", "offers", "offered", "available", "availability", "course", "courses", "training", "class", "classes",
        "program", "programs", "service", "services", "product", "products", "yes", "yeah", "yep", "yup", "sure",
        "no", "nope", "nah", "okay", "ok", "alright", "fine", "please", "actually", "also", "just", "really",
        "very", "there", "here", "today", "tomorrow", "yesterday", "your", "company", "companies", "our", "business",
        "language", "technology",
    }

    GENERAL_TOPIC_WORDS = {"weather", "recipe", "recipes", "joke", "cricket", "football", "soccer", "movie", "movies", "song", "songs", "news"}
    GENERAL_PHRASES = {
        "hello", "hi", "hey", "thanks", "thank you", "bye", "goodbye", "what is your name", "whats your name",
        "who are you", "what can you do", "how can you help me", "how can you help",
    }
    COMPANY_WIDE_PHRASES = {
        "what courses do you offer", "which courses do you offer", "what services do you offer", "which services do you offer",
        "what products do you offer", "which products do you offer", "what do you offer", "what does your company offer",
        "what are your services", "what are your products", "what are your courses", "what courses are available",
        "which courses are available", "what training do you offer", "which training do you offer", "what programs do you offer",
        "which programs do you offer",
    }

    FEE_PHRASES = {"how much", "how much fee", "how much does", "what is the fee", "what are the fees", "fee details", "fees", "fee", "price", "pricing", "cost", "costs", "tuition"}
    DISCOUNT_PHRASES = {"discount", "discounts", "reduce the fee", "reduce fee", "fee reduction", "concession"}
    TOPIC_PHRASES = {"what topics", "what topic", "topics covered", "topics", "what does it cover", "what is covered", "what are covered", "course content", "content"}
    DURATION_PHRASES = {"how long", "duration", "how many months", "how many days", "length of the course", "course duration"}
    TIMING_PHRASES = {"timing", "timings", "time", "schedule", "batch timing", "batch timings", "class timing", "class timings", "when is the class", "when are the classes"}
    AVAILABILITY_PHRASES = {"do you offer", "do you have", "is it available", "are you offering", "available", "availability", "offer", "offers"}
    MODE_PHRASES = {"online", "offline", "classroom", "mode", "online or classroom", "online and classroom"}
    ADMISSION_PHRASES = {"admission", "admissions", "registration", "enrollment", "enrolment", "when can i join", "when can i register", "when does it start", "when is the batch", "batch starts", "batch started", "started"}
    CONTACT_PHRASES = {"contact", "phone", "mobile", "email", "address", "location", "reach you", "contact details"}
    COMPANY_INFO_PHRASES = {"company name", "your name", "what is your company", "what's your company", "who are you", "about your company"}
    FULL_DETAILS_PHRASES = {"complete details", "full details", "all details", "everything about", "tell me everything", "complete information", "full information", "all information", "give me complete", "give me full details"}

    INTENT_GENERAL = "general"
    INTENT_AVAILABILITY = "availability"
    INTENT_FEE = "fee"
    INTENT_DISCOUNT = "discount"
    INTENT_TOPICS = "topics"
    INTENT_DURATION = "duration"
    INTENT_TIMINGS = "timings"
    INTENT_DURATION_AND_TIMINGS = "duration_and_timings"
    INTENT_MODE = "mode"
    INTENT_ADMISSION = "admission"
    INTENT_CONTACT = "contact"
    INTENT_COMPANY_INFO = "company_information"
    INTENT_COMPANY_COURSES = "company_courses"
    INTENT_DETAILS = "details"
    INTENT_CONFIRMATION = "confirmation"
    INTENT_UNKNOWN = "unknown"
    RESPONSE_SHORT = "short"
    RESPONSE_MEDIUM = "medium"
    RESPONSE_LONG = "long"

    def __init__(self, message_limit: int = DEFAULT_MESSAGE_LIMIT) -> None:
        self.message_limit = max(1, message_limit)

    def classify_message(self, message: str) -> str:
        normalized = self._normalize_text(message)
        if not normalized:
            return "unclear"
        if self._looks_like_gibberish(message):
            return "unclear"
        if self.is_negative_confirmation(message):
            return "negative_confirmation"
        if self._is_company_wide_question(message):
            return "company_general"
        if self._contains_any_phrase(message, self.COMPANY_INFO_PHRASES):
            return "company_general"
        if normalized in {"tell me", "tell me more", "go ahead", "more", "please tell me"}:
            return "follow_up"
        if self._is_general_question(message):
            return "general"
        if self._looks_like_follow_up(message):
            return "follow_up"
        if self.is_confirmation(message) and normalized in self.CONFIRMATION_WORDS:
            return "confirmation"
        subject_terms = self._extract_subject_terms(message)
        if subject_terms:
            return "new_topic"
        if len(normalized.split()) <= 3:
            return "follow_up"
        return "general"

    def analyze_message(self, message: str, messages=None) -> dict:
        message = (message or "").strip()
        previous_messages = messages or []
        message_type = self.classify_message(message)
        previous_subject = self.get_current_subject(previous_messages)
        explicit_subject = self.extract_subject(message)
        if explicit_subject:
            subject = explicit_subject
        elif message_type in {"follow_up", "confirmation"}:
            subject = previous_subject
        else:
            subject = None
        intent = self.detect_intent(message)
        response_style = self.detect_response_style(message, intent=intent, question_count=self.count_questions(message))
        requires_knowledge = self.requires_knowledge(message_type=message_type, intent=intent)
        retrieval_query = self.build_retrieval_query(current_message=message, messages=previous_messages)
        return {
            "message_type": message_type, "subject": subject, "explicit_subject": explicit_subject,
            "previous_subject": previous_subject, "intent": intent, "response_style": response_style,
            "requires_knowledge": requires_knowledge, "question_count": self.count_questions(message),
            "is_confirmation": message_type == "confirmation", "is_negative_confirmation": message_type == "negative_confirmation",
            "retrieval_query": retrieval_query,
        }

    def detect_intent(self, message: str) -> str:
        normalized = self._normalize_text(message)
        if not normalized:
            return self.INTENT_UNKNOWN
        if self._contains_any_phrase(normalized, self.COMPANY_INFO_PHRASES):
            return self.INTENT_COMPANY_INFO
        if self._contains_any_phrase(normalized, self.FULL_DETAILS_PHRASES):
            return self.INTENT_DETAILS
        has_duration = self._contains_any_phrase(normalized, self.DURATION_PHRASES)
        has_timings = self._contains_any_phrase(normalized, self.TIMING_PHRASES)
        if has_duration and has_timings:
            return self.INTENT_DURATION_AND_TIMINGS
        if self._contains_any_phrase(normalized, self.DISCOUNT_PHRASES):
            return self.INTENT_DISCOUNT
        if self._contains_any_phrase(normalized, self.FEE_PHRASES):
            return self.INTENT_FEE
        if self._contains_any_phrase(normalized, self.TOPIC_PHRASES):
            return self.INTENT_TOPICS
        if has_duration:
            return self.INTENT_DURATION
        if has_timings:
            return self.INTENT_TIMINGS
        if self._contains_any_phrase(normalized, self.ADMISSION_PHRASES):
            return self.INTENT_ADMISSION
        if self._contains_any_phrase(normalized, self.MODE_PHRASES):
            return self.INTENT_MODE
        if self._contains_any_phrase(normalized, self.CONTACT_PHRASES):
            return self.INTENT_CONTACT
        if self._is_company_wide_question(normalized):
            return self.INTENT_COMPANY_COURSES
        if self._contains_any_phrase(normalized, self.AVAILABILITY_PHRASES):
            return self.INTENT_AVAILABILITY
        if self.is_confirmation(normalized) and normalized in self.CONFIRMATION_WORDS:
            return self.INTENT_CONFIRMATION
        return self.INTENT_GENERAL

    def detect_response_style(self, message: str, intent: str | None = None, question_count: int | None = None) -> str:
        normalized = self._normalize_text(message)
        if not normalized:
            return self.RESPONSE_SHORT
        question_count = self.count_questions(message) if question_count is None else question_count
        if self._contains_any_phrase(normalized, self.FULL_DETAILS_PHRASES):
            return self.RESPONSE_LONG
        if question_count >= 3:
            return self.RESPONSE_LONG
        if question_count == 2:
            return self.RESPONSE_MEDIUM
        if self._contains_any_phrase(normalized, {"tell me about", "tell me more about", "explain the course", "explain everything", "course details", "details about", "more information about", "give me information"}):
            return self.RESPONSE_MEDIUM
        if intent in {self.INTENT_TOPICS, self.INTENT_DURATION_AND_TIMINGS, self.INTENT_DETAILS}:
            return self.RESPONSE_MEDIUM
        if intent == self.INTENT_COMPANY_COURSES:
            return self.RESPONSE_MEDIUM
        return self.RESPONSE_SHORT

    @staticmethod
    def requires_knowledge(message_type: str, intent: str) -> bool:
        if message_type in {"unclear", "general", "confirmation", "negative_confirmation"}:
            return False
        if message_type in {"new_topic", "follow_up", "company_general"}:
            return True
        if intent in {ContextService.INTENT_GENERAL, ContextService.INTENT_CONFIRMATION}:
            return False
        return True

    def extract_subject(self, message: str) -> str | None:
        normalized = self._normalize_text(message)
        if normalized in {"tell me", "tell me more", "go ahead", "more", "please tell me"}:
            return None
        terms = self._extract_subject_terms(message)
        # Strip common intent words from compound subject extraction so that
        # "What are the timings for Python?" resolves to "python".
        intent_tokens = set().union(
            *(set(re.findall(r"[a-z0-9+#.-]+", self._normalize_text(phrase))) for phrase in (
                self.FEE_PHRASES, self.DISCOUNT_PHRASES, self.TOPIC_PHRASES,
                self.DURATION_PHRASES, self.TIMING_PHRASES, self.MODE_PHRASES,
                self.ADMISSION_PHRASES, self.CONTACT_PHRASES, self.AVAILABILITY_PHRASES,
            ))
        )
        filtered = [term for term in terms if term not in intent_tokens and term not in {"course", "courses", "training", "program", "programs", "service", "services"}]
        if not filtered and terms and len(terms) == 1 and terms[0] not in intent_tokens:
            filtered = terms
        return " ".join(filtered[: self.MAX_SUBJECT_TERMS]) if filtered else None

    def _is_company_wide_question(self, message: str) -> bool:
        normalized = self._normalize_text(message)
        if not normalized:
            return False
        if normalized in self.COMPANY_WIDE_PHRASES:
            return True
        patterns = (
            r"^what (courses|services|products) do you offer$",
            r"^which (courses|services|products) do you offer$",
            r"^what do you offer$",
            r"^what are your (courses|services|products)$",
            r"^(what|which) courses (does|do) (your|the) company offer$",
            r"^(what|which) courses are (you|your company) offering$",
            r"^(what|which) services (does|do) (your|the) company offer$",
            r"^what does your company offer$",
            r"^what are you offering$",
        )
        return any(re.search(pattern, normalized) for pattern in patterns) or (
            any(word in normalized for word in ("course", "courses", "training", "program", "programs"))
            and any(word in normalized for word in ("offer", "offers", "offering", "provide", "provides", "available"))
            and any(word in normalized for word in ("your company", "the company", "your business"))
        )

    def _looks_like_follow_up(self, message: str) -> bool:
        normalized = self._normalize_text(message)
        if not normalized:
            return False
        if normalized in {"tell me", "tell me more", "go ahead", "more", "please tell me"}:
            return True
        if self._is_company_wide_question(message) or self._is_general_question(message):
            return False
        words = set(re.findall(r"[A-Za-z0-9+#.-]+", normalized))
        # A terse question like "How much?" should always be interpreted as
        # context-dependent, even though "much" has no explicit subject.
        if len(words) <= 3 and any(word in words for word in self.FOLLOW_UP_WORDS):
            return True
        return bool(words & self.FOLLOW_UP_WORDS) and not self._extract_subject_terms(message)

    def _contains_fuzzy_intent_word(self, normalized: str) -> bool:
        words = re.findall(r"[a-zA-Z]+", normalized)
        intent_words = ("timing", "timings", "topics", "topic", "details", "detail", "duration", "fees", "fee", "price", "pricing", "cost", "syllabus", "schedule", "admission", "availability", "available")
        return any(self._similarity_ratio(word, target) >= 0.78 for word in words for target in intent_words)

    def get_current_subject(self, messages) -> str | None:
        normalized = self._normalize_messages(messages)
        for index in range(len(normalized) - 1, -1, -1):
            item = normalized[index]
            if item["role"] != "user":
                continue
            content = item["content"]
            if index > 0 and normalized[index - 1]["role"] == "assistant" and self._is_lead_detail_question(normalized[index - 1]["content"]):
                continue
            message_type = self.classify_message(content)
            if message_type == "new_topic":
                subject = self.extract_subject(content)
                if subject:
                    return subject
        return None

    @staticmethod
    def _is_lead_detail_question(message: str) -> bool:
        text = " ".join((message or "").lower().split())
        return any(phrase in text for phrase in ("your name", "phone number", "mobile number", "contact number", "email address", "email id", "share your email", "share your phone"))

    def build_retrieval_query(self, current_message: str, messages=None) -> str:
        message = (current_message or "").strip()
        previous_messages = self._normalize_messages(messages)
        subject = self.get_current_subject(previous_messages)
        if not subject:
            return message[: self.MAX_RETRIEVAL_QUERY_LENGTH]
        return self._build_query_with_subject(message, subject)

    def _build_query_with_subject(self, message: str, subject: str) -> str:
        normalized = self._normalize_text(message)
        if subject and subject in normalized:
            return message[: self.MAX_RETRIEVAL_QUERY_LENGTH]
        return f"{subject} {message}"[: self.MAX_RETRIEVAL_QUERY_LENGTH]

    def _extract_subject_terms(self, message: str) -> list[str]:
        normalized = self._normalize_text(message)
        if not normalized or self._is_general_question(message) or self._is_company_wide_question(message):
            return []
        if normalized in {"tell me", "tell me more", "go ahead", "more", "please tell me"}:
            return []
        tokens = re.findall(r"[A-Za-z0-9+#.-]+", normalized)
        terms = []
        for token in tokens:
            if token in self.STOP_WORDS or len(token) <= 1 or token in terms:
                continue
            terms.append(token)
        return terms

    def _is_general_question(self, message: str) -> bool:
        normalized = self._normalize_text(message)
        if normalized in self.GENERAL_PHRASES:
            return True
        return bool(set(re.findall(r"[a-z0-9]+", normalized)) & self.GENERAL_TOPIC_WORDS)

    def _looks_like_gibberish(self, message: str) -> bool:
        normalized = self._normalize_text(message)
        if not normalized:
            return True
        alnum = re.findall(r"[a-zA-Z0-9]+", normalized)
        return not alnum or (len(normalized) <= 6 and not any(char.isalpha() for char in normalized))

    def _contains_any_phrase(self, text: str, phrases) -> bool:
        normalized = self._normalize_text(text)
        for phrase in phrases:
            phrase_normalized = self._normalize_text(phrase)
            if re.search(rf"(?<!\w){re.escape(phrase_normalized)}(?!\w)", normalized):
                return True
        return False

    def is_confirmation(self, message: str) -> bool:
        return self._normalize_text(message) in self.CONFIRMATION_WORDS

    def is_negative_confirmation(self, message: str) -> bool:
        return self._normalize_text(message) in self.NEGATIVE_CONFIRMATION_WORDS

    @staticmethod
    def _normalize_text(text: str) -> str:
        return " ".join(str(text or "").lower().replace("’", "'").split()).rstrip("?!.,;:").strip()

    @staticmethod
    def _normalize_messages(messages) -> list[dict[str, str]]:
        normalized = []
        for item in list(messages or []):
            role = item.get("role") if isinstance(item, dict) else getattr(item, "role", None)
            content = item.get("content") if isinstance(item, dict) else getattr(item, "content", None)
            if role and content:
                normalized.append({"role": str(role).lower(), "content": str(content).strip()})
        return normalized[-ContextService.MAX_CONTEXT_MESSAGES :]

    @staticmethod
    def _similarity_ratio(first: str, second: str) -> float:
        if not first or not second:
            return 0.0
        import difflib
        return difflib.SequenceMatcher(None, first.lower(), second.lower()).ratio()

    def count_questions(self, message: str) -> int:
        return max(1, (message or "").count("?")) if (message or "").strip() else 0
