from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.services.conversation_guard import ConversationGuard
from app.services.retrieval_service import RetrievalService


def test_programming_is_a_subject_qualifier():
    item = SimpleNamespace(
        title="Python Programming",
        category="course",
        content="Python syntax and fundamentals",
    )
    assert ConversationGuard.matches_subject("Python Programming", item)


def test_retrieval_falls_back_to_selected_scoped_record_when_search_misses():
    item = SimpleNamespace(
        id=11,
        title="Python Programming",
        category="course",
        content="Topics: Python syntax, variables, functions, OOP",
        semantic_distance=None,
    )
    knowledge = MagicMock()
    knowledge.search.return_value = []
    knowledge.get_all.return_value = [item]

    service = RetrievalService(knowledge)
    service.ranker.rank = MagicMock(return_value=[item])

    result = service.retrieve(
        organization_id=1,
        query="Python Programming topics syllabus covered",
        subject="Python Programming",
        agent_id=13,
        limit=4,
    )

    assert result == [item]
    knowledge.search.assert_called_once()
    knowledge.get_all.assert_called_once_with(
        organization_id=1,
        agent_id=13,
        scope="available",
    )
