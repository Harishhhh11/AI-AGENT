"""Behavioral contracts for Phase 2 conversation intelligence."""

from app.services.conversation_subject_service import ConversationSubjectService
from app.services.response_policy_service import ResponsePolicyService
from app.services.relevance_service import RelevanceService
from app.services.grounding_service import GroundingService


def test_subject_switches_without_company_specific_vocabulary() -> None:
    service = ConversationSubjectService()

    first = service.resolve(
        message="Tell me about Python",
        intent="availability",
        previous_messages=[],
    )
    second = service.resolve(
        message="What about Java?",
        intent="availability",
        previous_messages=[
            {"role": "user", "content": "Tell me about Python"},
        ],
        previous_subject=first.current_subject,
    )

    assert first.current_subject == "python"
    assert second.current_subject == "java"
    assert second.is_topic_switch is True


def test_follow_up_inherits_previous_subject() -> None:
    service = ConversationSubjectService()

    result = service.resolve(
        message="How much?",
        intent="fee",
        previous_messages=[
            {"role": "user", "content": "Tell me about Python"},
        ],
        previous_subject="python",
    )

    assert result.current_subject == "python"
    assert result.explicit_subject is None
    assert result.is_topic_switch is False


def test_relevance_rejects_unrelated_knowledge() -> None:
    service = RelevanceService()

    decision = service.score(
        query="python course fee",
        title="Company address",
        content="Nawabpet, Nellore",
        semantic_distance=None,
    )

    assert decision.accepted is False


def test_grounding_rejects_retrieval_without_relevant_signal() -> None:
    relevance = RelevanceService()
    grounding = GroundingService(relevance_service=relevance)

    decision = grounding.evaluate(
        query="python course fee",
        title="Company address",
        content="Nawabpet, Nellore",
        semantic_distance=None,
    )

    assert decision.accepted is False


def test_response_policy_scales_with_requested_detail() -> None:
    policy = ResponsePolicyService()

    short = policy.plan(
        message="How much?",
        intent="fee",
        question_count=1,
        requires_knowledge=True,
    )
    detailed = policy.plan(
        message="Explain the syllabus and duration in detail",
        intent="topics",
        question_count=1,
        requires_knowledge=True,
    )

    assert short.style == "short"
    assert detailed.style in {"medium", "long"}
