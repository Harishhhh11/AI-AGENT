import pytest

from app.services.answer_orchestrator import AnswerOrchestrator
from app.services.knowledge_answer_service import KnowledgeAnswerService
from app.services.semantic_conversation_service import SemanticConversation


class FakeLLM:
    def __init__(self, answer):
        self.answer = answer

    async def generate(self, prompt):
        return self.answer


@pytest.mark.asyncio
async def test_multi_question_answer_uses_llm_with_verified_context():
    orchestrator = AnswerOrchestrator(FakeLLM("Java costs INR 25,000. Python batches run 10 AM to 11 AM."), KnowledgeAnswerService())
    semantic = SemanticConversation(
        intent="multi_part",
        subject=None,
        questions=[
            {"text": "What is the fee for Java?", "intent": "fee", "subject": "Java Programming"},
            {"text": "What are the Python timings?", "intent": "timings", "subject": "Python Programming"},
        ],
        response_style="medium",
        requires_knowledge=True,
        wants_lead_action=False,
    )
    result = await orchestrator.compose(
        semantic=semantic,
        original_message="What is the fee for Java and Python timings?",
        conversation_context="",
        scoped_items=[type("Item", (), {"title": "Java", "content": "Course Fee: INR 25,000"})(), type("Item", (), {"title": "Python", "content": "Batch timings: 10:00 AM to 11:00 AM"})()],
        response_style="medium",
    )
    assert result == "Java costs INR 25,000. Python batches run 10 AM to 11 AM."
