import src.orchestration.nodes.synthesizer as synthesizer_module
from src.orchestration.nodes.synthesizer import _build_system_prompt, _synthesize


class CloudClient:
    model = "test-cloud"

    def generate(self, system_prompt, user_prompt, conversation_history=None):
        return "cloud answer"


def test_system_prompt_uses_minimised_evidence_packet():
    prompt = _build_system_prompt(
        user_tier=1,
        sources=["structured", "rag"],
        sql_results=[
            {
                "name": "Dr. Rao",
                "email": "rao@example.org",
                "full_text": "raw full document should not leave",
                "research_area": "Robotics",
            }
        ],
        chunks=[
            {
                "chunk_id": "ch_1",
                "publication_id": "pub_1",
                "title": "Robotics",
                "content": "x" * 1000,
            }
        ],
        context_summary="",
    )

    assert "rao@example.org" not in prompt
    assert "raw full document should not leave" not in prompt
    assert "x" * 800 not in prompt
    assert "SQL Evidence" in prompt
    assert "Document Evidence" in prompt


def test_cloud_synthesis_is_explicitly_gated(monkeypatch):
    monkeypatch.delenv("CLOUD_SYNTHESIS_ALLOWED", raising=False)
    monkeypatch.setattr(synthesizer_module, "get_llm_client", lambda: CloudClient())
    monkeypatch.setattr(synthesizer_module, "get_local_llm_client", lambda: None)
    monkeypatch.setattr(synthesizer_module, "log_llm_call", lambda *args, **kwargs: None)

    response, provenance = _synthesize(
        query="Find robotics researchers",
        sources=["structured"],
        sql_results=[{"name": "Dr. Rao"}],
        chunks=[],
        user_tier=1,
        context_summary="",
    )

    assert response != "cloud answer"
    assert provenance == {"synth": "rule_based", "cloud_synthesis_used": False}


def test_cloud_synthesis_reports_provenance_when_allowed(monkeypatch):
    monkeypatch.setenv("CLOUD_SYNTHESIS_ALLOWED", "true")
    monkeypatch.setattr(synthesizer_module, "get_llm_client", lambda: CloudClient())
    monkeypatch.setattr(synthesizer_module, "log_llm_call", lambda *args, **kwargs: None)

    response, provenance = _synthesize(
        query="Find robotics researchers",
        sources=["structured"],
        sql_results=[{"name": "Dr. Rao"}],
        chunks=[],
        user_tier=1,
        context_summary="",
    )

    assert response == "cloud answer"
    assert provenance == {"synth": "cloud_llm", "cloud_synthesis_used": True}
