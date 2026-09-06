from collections import Counter
from types import SimpleNamespace

from app.services.analytics_service import AnalyticsService


def test_normalize_and_rank_questions():
    assert AnalyticsService._normalize_question("  How much? ") == "how much"
    ranked = AnalyticsService._rank(
        Counter({"where are you?": 3, "hello": 1})
    )
    assert ranked[0].question == "where are you?"
    assert ranked[0].count == 3


def test_unanswered_reply_detection():
    user_message = SimpleNamespace(conversation_id=1, id=1)
    assistant_message = SimpleNamespace(
        conversation_id=1,
        id=2,
        content="I don't know that yet.",
    )
    assert AnalyticsService._has_unanswered_reply(
        user_message,
        [assistant_message],
    )
