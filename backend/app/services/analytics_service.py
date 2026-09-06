"""Tenant-scoped conversation and lead analytics."""

from collections import Counter
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.lead import Lead
from app.models.message import Message
from app.schemas.analytics import (
    AnalyticsOverview,
    LeadMetrics,
    MetricSummary,
    RankedQuestion,
)


_UNANSWERED_MARKERS = (
    "i don't know",
    "i do not know",
    "not sure",
    "unable to answer",
    "don't have that information",
    "do not have that information",
    "cannot help with that",
)


class AnalyticsService:
    """Build analytics from organization-owned conversations and leads."""

    def __init__(self, db: Session):
        self.db = db

    def overview(self, organization_id: int) -> AnalyticsOverview:
        conversations = list(
            self.db.scalars(
                select(Conversation)
                .where(Conversation.organization_id == organization_id)
                .order_by(Conversation.created_at.desc())
            )
        )
        conversation_ids = [conversation.id for conversation in conversations]
        messages = (
            list(
                self.db.scalars(
                    select(Message).where(
                        Message.conversation_id.in_(conversation_ids)
                    )
                )
            )
            if conversation_ids
            else []
        )
        leads = list(
            self.db.scalars(
                select(Lead)
                .where(Lead.organization_id == organization_id)
            )
        )

        user_messages = [message for message in messages if message.role == "user"]
        assistant_messages = [
            message for message in messages if message.role == "assistant"
        ]
        counts = Counter(self._normalize_question(message.content) for message in user_messages)
        popular_questions = self._rank(counts)

        unanswered_counts = Counter(
            self._normalize_question(user_message.content)
            for user_message in user_messages
            if self._has_unanswered_reply(user_message, assistant_messages)
        )

        completed_conversations = sum(
            conversation.status in {"completed", "closed"} for conversation in conversations
        )
        active_conversations = sum(
            conversation.status not in {"completed", "closed"} for conversation in conversations
        )
        completed_messages = sum(
            message.role == "assistant" for message in messages
        )
        qualified = sum(lead.status in {"qualified", "converted", "won"} for lead in leads)
        converted = sum(lead.status in {"converted", "won"} for lead in leads)

        return AnalyticsOverview(
            conversations=MetricSummary(
                total=len(conversations),
                active=active_conversations,
                completed=completed_conversations,
                average_per_conversation=round(
                    len(messages) / len(conversations), 2
                )
                if conversations
                else 0.0,
            ),
            messages=MetricSummary(
                total=len(messages),
                active=len(user_messages),
                completed=completed_messages,
                average_per_conversation=round(
                    len(messages) / len(conversations), 2
                )
                if conversations
                else 0.0,
            ),
            leads=LeadMetrics(
                total=len(leads),
                new=sum(lead.status == "new" for lead in leads),
                qualified=qualified,
                converted=converted,
            ),
            conversion_rate=round(
                (converted / len(conversations)) * 100, 2
            )
            if conversations
            else 0.0,
            popular_questions=popular_questions,
            unanswered_questions=self._rank(unanswered_counts),
        )

    @staticmethod
    def _normalize_question(content: str) -> str:
        normalized = re.sub(r"\s+", " ", content.strip().lower())
        return normalized.rstrip("?!.,")

    @staticmethod
    def _rank(counts: Counter[str], limit: int = 10) -> list[RankedQuestion]:
        return [
            RankedQuestion(question=question, count=count)
            for question, count in counts.most_common(limit)
            if question
        ]

    @staticmethod
    def _has_unanswered_reply(user_message: Message, assistant_messages: list[Message]) -> bool:
        replies = [
            message
            for message in assistant_messages
            if message.conversation_id == user_message.conversation_id
            and message.id > user_message.id
        ]
        if not replies:
            return True
        return any(
            marker in replies[0].content.lower() for marker in _UNANSWERED_MARKERS
        )
