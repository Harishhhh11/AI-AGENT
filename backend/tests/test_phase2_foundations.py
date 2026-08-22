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
    policy = ResponsePolicyService()
    assert policy.plan(message="What is the fee?", intent="fee").style == policy.SHORT
    assert policy.plan(
        message="What is the fee and duration?",
        intent="duration_and_timings",
        question_count=2,
    ).style == policy.MEDIUM
    assert policy.plan(
        message="Give me complete details about the service.",
        intent="details",
    ).style == policy.LONG


def test_relevance_rejects_unrelated_subject() -> None:
    result = RelevanceService().score(
        query="hotel management",
        title="Python programming",
        content="Programming fundamentals and data analysis.",
        semantic_distance=0.50,
    )
    assert result.accepted is False


def test_relevance_accepts_strong_match() -> None:
    result = RelevanceService().score(
        query="return policy",
        title="Return policy",
        content="Unused products can be returned within 30 days.",
        semantic_distance=0.30,
    )
    assert result.accepted is True


def test_grounding_wraps_relevance_decision() -> None:
    decision = GroundingService().evaluate(
        query="return policy",
        title="Return policy",
        content="Unused products can be returned within 30 days.",
        semantic_distance=0.30,
    )
    assert decision.accepted is True
    assert decision.reason == "accepted"


def test_grounding_rejects_unrelated_content() -> None:
    decision = GroundingService().evaluate(
        query="pricing",
        title="Technical support",
        content="Technical support is available during business hours.",
    )
    assert decision.accepted is False
    assert decision.reason == "insufficient relevance"
