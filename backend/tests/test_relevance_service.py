from app.services.relevance_service import RelevanceService


def test_plural_question_matches_singular_knowledge_label() -> None:
    result = RelevanceService().score(
        query="Which courses do you offer?",
        title="MT-DOC",
        content="Course: Python Programming",
    )
    assert result.accepted is True


def test_strong_semantic_match_can_accept_a_paraphrase_without_shared_keywords() -> None:
    result = RelevanceService().score(
        query="How long can I study before finishing it?",
        title="Python Program",
        content="The training runs for 12 weeks.",
        semantic_distance=0.30,
    )
    assert result.matched_terms == ()
    assert result.accepted is True


def test_weak_semantic_match_is_not_enough_without_lexical_evidence() -> None:
    result = RelevanceService().score(
        query="How long can I study before finishing it?",
        title="Unrelated service",
        content="Annual maintenance plans for office printers.",
        semantic_distance=0.70,
    )
    assert result.accepted is False
