import json


class FakeVerifierClient:
    model = "fake-verifier"

    def __init__(self, ok=True):
        self.ok = ok

    def generate(self, system_prompt, user_prompt, conversation_history):
        assert "verify that every cited claim" in system_prompt.lower()
        assert "[cite:pub_1:ch_1]" in user_prompt
        return json.dumps({"ok": self.ok, "unsupported_claims": [] if self.ok else ["bad claim"]})


def test_verifier_node_marks_cited_answer_ok(monkeypatch):
    import src.orchestration.nodes.verifier as verifier_module

    monkeypatch.setattr(verifier_module, "get_llm_client", lambda: FakeVerifierClient(ok=True))

    result = verifier_module.verifier_node(
        {
            "synthesized_response": "Robotics is active [cite:pub_1:ch_1].",
            "retrieved_chunks": [
                {
                    "publication_id": "pub_1",
                    "chunk_id": "ch_1",
                    "chunk_text": "Robotics is active in Gujarat.",
                }
            ],
            "verification_retries": 0,
        }
    )

    assert result["verification_status"] == "ok"
    assert result["unsupported_claims"] == []


def test_verifier_node_requests_one_retry_on_failure(monkeypatch):
    import src.orchestration.nodes.verifier as verifier_module

    monkeypatch.setattr(verifier_module, "get_llm_client", lambda: FakeVerifierClient(ok=False))

    result = verifier_module.verifier_node(
        {
            "synthesized_response": "Unsupported claim [cite:pub_1:ch_1].",
            "retrieved_chunks": [
                {
                    "publication_id": "pub_1",
                    "chunk_id": "ch_1",
                    "chunk_text": "Different evidence.",
                }
            ],
            "verification_retries": 0,
        }
    )

    assert result["verification_status"] == "retry"
    assert result["verification_retries"] == 1
    assert result["unsupported_claims"] == ["bad claim"]
