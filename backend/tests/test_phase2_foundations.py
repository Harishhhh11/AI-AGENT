"""Focused tests for Phase 2 conversation-intelligence foundations."""

from app.services.conversation_subject_service import ConversationSubjectService
from app.services.grounding_service import GroundingService
from app.services.relevance_service import RelevanceService
from app.services.response_policy_service import ResponsePolicyService


def test_follow_up_preserves_previous_subject() -> None:
    result = ConversationSubjectService().resolve(
        message="How much?",
        intent="fee",
        previous_messages=[
            {"role": "user", "content": "Tell me about the analytics platform"},
        ],
    )
    assert result.current_subject == "analytics platform"
    assert result.previous_subject == "analytics platform"
    assert result.is_topic_switch is False


def test_explicit_subject_switch() -> None:
    result = ConversationSubjectService().resolve(
        message="What about the mobile app?",
        intent="details",
        previous_messages=[
            {"role": "user", "content": "Tell me about the analytics platform"},
        ],
    )
    assert result.current_subject == "mobile app"
    assert result.previous_subject == "analytics platform"
    assert result.is_topic_switch is True


def test_response_policy_has_bounded_styles() -> None:
    service = ResponsePolicyService()
    short_plan = service.plan(message="What is the fee?", intent="fee")
    medium_plan = service.plan(
        message="What is the duration and timing?",
        intent="duration_and_timings",
        question_count=2,
    )
    long_plan = service.plan(
        message="Give me complete details",
        intent="details",
    )
    assert short_plan.style == service.SHORT
    assert short_plan.max_characters == 350
    assert medium_plan.style == service.MEDIUM
    assert long_plan.style == service.LONG


def test_relevance_accepts_strong_title_match() -> None:
    result = RelevanceService().score(
        query="analytics platform",
        title="Analytics Platform",
        content="Overview and capabilities",
    )
    assert result.accepted is True
    assert result.lexical_score >= 0.60


def test_relevance_rejects_unrelated_knowledge() -> None:
    result = RelevanceService().score(
        query="analytics platform",
        title="Cooking recipe",
        content="Ingredients and preparation steps",
    )
    assert result.accepted is False


def test_grounding_delegates_to_relevance() -> None:
    decision = GroundingService().evaluate(
        query="analytics platform",
        title="Analytics Platform",
        content="Capabilities and pricing",
    )
    assert decision.accepted is True
    assert decision.reason == "accepted"
    assert decision.score >= 0.60
