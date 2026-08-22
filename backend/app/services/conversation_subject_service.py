"""Company-agnostic conversational subject tracking."""

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class SubjectResolution:
    current_subject: str | None
    explicit_subject: str | None
    previous_subject: str | None
    is_topic_switch: bool
    confidence: float


class ConversationSubjectService:
    """Resolve follow-up subjects and topic switches without company vocabulary."""

    FOLLOW_UP_INTENTS = {
        "fee", "discount", "topics", "duration", "timings",
        "duration_and_timings", "mode", "admission", "contact",
        "details", "availability", "company_information",
    }

    STOP_WORDS = {
        "a", "an", "the", "is", "are", "am", "was", "were", "do", "does", "did",
        "you", "your", "we", "our", "i", "me", "my", "to", "of", "for", "from",
        "in", "on", "at", "by", "with", "about", "and", "or", "but", "can", "could",
        "would", "should", "will", "may", "might", "what", "which", "who", "where",
        "when", "why", "how", "much", "many", "more", "details", "detail", "information",
        "info", "offer", "offers", "available", "availability", "course", "courses", "service",
        "services", "product", "products", "program", "programs", "training", "class", "classes",
        "online", "offline", "classroom", "mode", "fee", "fees", "price", "pricing", "cost",
        "costs", "duration", "timing", "timings", "schedule", "topics", "topic", "covered",
        "cover", "syllabus", "contact", "phone", "email", "address", "location", "admission",
        "admissions", "registration", "batch", "started", "start", "yes", "yeah", "yep", "sure",
        "okay", "ok", "please", "this", "that", "it", "its", "tell", "give", "show", "share",
    }

    SUBJECT_QUALIFIERS = {
        "program", "programs", "service", "services", "product", "products", "course", "courses",
        "solution", "solutions", "package", "packages", "plan", "plans", "model", "models",
        "subscription", "subscriptions", "software", "platform", "device", "devices",
    }

    def resolve(self, *, message: str, intent: str, previous_messages: list[dict] | None, previous_subject: str | None = None) -> SubjectResolution:
        text = self._normalize(message)
        explicit = self.extract_subject(text)
        previous = previous_subject or self.subject_from_history(previous_messages or [])
        if explicit:
            switched = bool(previous and explicit != previous)
            return SubjectResolution(explicit, explicit, previous, switched, 0.98 if switched or not previous else 0.95)
        if intent in self.FOLLOW_UP_INTENTS and previous:
            return SubjectResolution(previous, None, previous, False, 0.90)
        if self.is_generic_follow_up(text) and previous:
            return SubjectResolution(previous, None, previous, False, 0.82)
        return SubjectResolution(None, None, previous, False, 0.0)

    def extract_subject(self, message: str) -> str | None:
        text = self._normalize(message)
        if not text:
            return None
        cleaned = re.sub(r"[^a-z0-9\s&+.#/-]", " ", text)
        candidates = [token for token in cleaned.split() if token not in self.STOP_WORDS and len(token) >= 2 and not token.isdigit()]
        if not candidates:
            return None
        words = candidates[:6]
        while len(words) > 1 and words[0] in self.SUBJECT_QUALIFIERS:
            words.pop(0)
        return " ".join(words) or None

    def subject_from_history(self, messages: list[dict]) -> str | None:
        for item in reversed(messages):
            if not isinstance(item, dict) or item.get("role") != "user":
                continue
            subject = self.extract_subject(str(item.get("content") or ""))
            if subject:
                return subject
        return None

    def is_generic_follow_up(self, message: str) -> bool:
        tokens = self._normalize(message).split()
        if not tokens:
            return False
        follow_up_terms = {
            "how", "much", "what", "which", "when", "where", "why", "details", "detail",
            "topics", "topic", "fee", "fees", "price", "pricing", "cost", "duration", "time",
            "timing", "timings", "mode", "online", "offline", "classroom", "availability",
            "available", "more", "syllabus", "covered", "cover", "schedule", "discount", "discounts",
        }
        return all(token in follow_up_terms for token in tokens)

    @staticmethod
    def _normalize(text: str) -> str:
        return " ".join((text or "").strip().lower().split())
