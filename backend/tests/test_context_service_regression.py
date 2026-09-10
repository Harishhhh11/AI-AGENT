from app.services.context_service import ContextService


def test_context_service_build_context_returns_bounded_transcript():
    service = ContextService()
    result = service.build_context(
        [
            {"role": "user", "content": "What is the Python fee?"},
            {"role": "assistant", "content": "The fee is INR 25,000."},
        ]
    )
    assert "USER: What is the Python fee?" in result
    assert "ASSISTANT: The fee is INR 25,000." in result


def test_context_service_build_context_handles_empty_history():
    assert ContextService().build_context([]) == "No previous conversation."
