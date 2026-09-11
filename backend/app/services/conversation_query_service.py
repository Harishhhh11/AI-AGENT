from __future__ import annotations

from app.services.conversation_subject_service import ConversationSubjectService
from app.services.semantic_conversation_service import SemanticConversation


class ConversationQueryService:
    """Convert semantic analysis into compact, subject-aware retrieval queries."""

    def __init__(self) -> None:
        self.subjects = ConversationSubjectService()

    def build_queries(
        self,
        *,
        semantic: SemanticConversation,
        fallback_subject: str | None,
        original_message: str,
    ) -> list[dict]:
        questions = semantic.questions or [
            {"text": original_message, "intent": semantic.intent, "subject": semantic.subject}
        ]
        queries: list[dict] = []
        active_subject = fallback_subject
        for question in questions[:8]:
            intent = str(question.get("intent") or semantic.intent or "general").lower()
            subject = str(question.get("subject") or active_subject or "").strip() or None
            if subject:
                active_subject = subject
            text = str(question.get("text") or original_message).strip()
            query = self._rewrite(text, subject, intent)
            queries.append({"text": text, "intent": intent, "subject": subject, "query": query})
        return queries

    @staticmethod
    def _rewrite(text: str, subject: str | None, intent: str) -> str:
        intent_terms = {
            "fee": "price fee cost tuition payment amount",
            "discount": "discount offer concession reduction",
            "duration": "duration length months weeks days",
            "timings": "timings schedule batch class time",
            "topics": "topics syllabus curriculum course content covered",
            "mode": "online offline classroom virtual remote mode",
            "certificate": "certificate certification completion certificate",
            "payment": "payment method pay installment installments advance full payment",
            "eligibility": "eligibility requirements qualification who can join",
            "admission": "admission enrollment registration join sign up",
            "contact": "contact phone mobile email address location",
            "company_courses": "courses programs training services products offered",
        }.get(intent, "")
        parts = [str(subject).strip(), intent_terms, text.strip()]
        return " ".join(part for part in parts if part)[:500]
