from src.orchestration.nodes.synthesizer import synthesizer_node


def test_synthesizer_uses_llm_client(monkeypatch):
    class FakeClient:
        def generate(self, system_prompt, user_prompt, conversation_history):
            assert "Tier 1" in system_prompt
            assert "Structured data: 1 records" in system_prompt
            assert "Prior Session Context" in system_prompt
            assert user_prompt == "User Query: Summarize robotics research in Gujarat"
            assert len(conversation_history) == 1
            return "Real LLM answer"

    monkeypatch.setattr(
        "src.orchestration.nodes.synthesizer.get_llm_client",
        lambda: FakeClient(),
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
    class FailingClient:
        def generate(self, system_prompt, user_prompt, conversation_history):
            raise RuntimeError("provider unavailable")

    monkeypatch.setattr(
        "src.orchestration.nodes.synthesizer.get_llm_client",
        lambda: FailingClient(),
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
