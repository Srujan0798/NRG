from src.orchestration.nodes.synthesizer import synthesizer_node


class FakeMeshClient:
    """Fake mesh wrapping FakeClient for synthesizer LLM tests."""

    def __init__(self):
        self._client = None

    def generate(self, system_prompt, user_prompt, conversation_history=None):
        assert "Tier 1" in system_prompt
        assert "Structured data: 1 records" in system_prompt
        assert "Prior Session Context" in system_prompt
        assert user_prompt == "User Query: Summarize robotics research in Gujarat"
        assert len(conversation_history) == 1
        return "Real LLM answer"

    def generate_streaming(self, system_prompt, user_prompt, conversation_history=None):
        response = self.generate(system_prompt, user_prompt, conversation_history)
        for chunk in response:
            yield chunk


def test_synthesizer_uses_llm_client(monkeypatch):
    fake_mesh = FakeMeshClient()
    monkeypatch.setattr(
        "src.orchestration.nodes.synthesizer.get_llm_mesh",
        lambda: fake_mesh,
    )
    # Allow cloud synthesis for this test
    monkeypatch.setenv("CLOUD_SYNTHESIS_ALLOWED", "true")

    result = synthesizer_node(
        {
            "user_query": "Summarize robotics research in Gujarat",
            "sql_results": [{"name": "Dr. Rao"}],
            "retrieved_chunks": ["Robotics research is growing."],
            "user_tier": 1,
            "conversation_history": [
                {"query": "Previous question", "response": "Previous answer"}
            ],
        }
    )

    assert result["synthesized_response"] == "Real LLM answer"
    assert result["verification_status"] is True


def test_synthesizer_falls_back_on_llm_failure(monkeypatch):
    class FailingMesh:
        def generate(self, system_prompt, user_prompt, conversation_history=None):
            raise RuntimeError("provider unavailable")

        def generate_streaming(self, system_prompt, user_prompt, conversation_history=None):
            raise RuntimeError("provider unavailable")

    monkeypatch.setattr(
        "src.orchestration.nodes.synthesizer.get_llm_mesh",
        lambda: FailingMesh(),
    )
    monkeypatch.setattr(
        "src.orchestration.nodes.synthesizer.get_local_llm_client",
        lambda: None,
    )

    result = synthesizer_node(
        {
            "user_query": "Summarize robotics research in Gujarat",
            "sql_results": [{"name": "Dr. Rao"}],
            "retrieved_chunks": ["Robotics research is growing."],
            "user_tier": 1,
            "conversation_history": [],
        }
    )

    assert "Fallback" in result["synthesized_response"]
    assert result["verification_status"] is True
