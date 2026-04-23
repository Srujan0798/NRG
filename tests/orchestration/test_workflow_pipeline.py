from src.orchestration.graph import NRGWorkflow
import src.orchestration.graph as graph_module
import src.orchestration.nodes.executor as executor_module
import src.orchestration.nodes.synthesizer as synthesizer_module


def _clear_query_cache():
    """Clear Redis query cache to prevent cross-test contamination."""
    try:
        from src.caching.redis_layer import _get_redis
        client = _get_redis()
        if client:
            for key in client.scan_iter(match="query:*"):
                client.delete(key)
    except Exception:
        pass


class StubTextToSQLSkill:
    def execute(self, user_query: str, user_tier: int = 1):
        return {
            "query": "SELECT * FROM researchers LIMIT 100",
            "results": [{"name": "Dr. Rao", "state": "GJ"}],
        }

    def close(self):
        return None


class StubRAGSkill:
    def retrieve(self, query: str, user_tier: int = 1, top_k: int = 5):
        return {
            "chunks": ["Robotics research in Gujarat is growing rapidly."],
            "metadata": [{"source_id": "doc-1", "source_type": "publication"}],
        }

    def close(self):
        return None


class FailingRAGSkill:
    def retrieve(self, query: str, user_tier: int = 1, top_k: int = 5):
        raise RuntimeError("Qdrant unavailable")

    def close(self):
        return None


def test_workflow_runs_full_orchestration_pipeline(monkeypatch):
    _clear_query_cache()
    # Clear executor skill caches so monkeypatch is respected
    executor_module._sql_skill_instance = None
    executor_module._sql_skill_class_id = None
    executor_module._rag_skill_instance = None
    executor_module._rag_skill_class_id = None

    monkeypatch.setattr(executor_module, "RAGSkill", FailingRAGSkill)

    monkeypatch.setattr(graph_module, "log_query", lambda *args, **kwargs: None)
    monkeypatch.setattr(executor_module, "log_sql", lambda *args, **kwargs: None)
    monkeypatch.setattr(synthesizer_module, "log_llm_call", lambda *args, **kwargs: None)
    monkeypatch.setattr(executor_module, "TextToSQLSkill", StubTextToSQLSkill)
    monkeypatch.setattr(executor_module, "RAGSkill", StubRAGSkill)
    monkeypatch.setattr(synthesizer_module, "get_llm_mesh", lambda: None)
    monkeypatch.setattr(synthesizer_module, "get_local_llm_client", lambda: None)

    workflow = NRGWorkflow()

    result = workflow.run(
        "Synthesize robotics researchers and trends in Gujarat",
        user_tier=1,
        session_id="research-session-1",
    )

    assert result["session_id"] == "research-session-1"
    assert result["intent"] == "hybrid"
    assert result["routing_decision"] == "text_to_sql+rag"
    assert result["sql_results"] == [{"name": "Dr. Rao", "state": "GJ"}]
    assert len(result["retrieved_chunks"]) == 1
    chunk = result["retrieved_chunks"][0]
    assert chunk["chunk_text"] == "Robotics research in Gujarat is growing rapidly."
    assert result["provenance"] == {
        "synth": "rule_based",
        "cloud_synthesis_used": False,
    }
    assert "Fallback" in result["synthesized_response"] or "Structured summary" in result["synthesized_response"] or "synthesized" in result["synthesized_response"].lower()
    assert result["conversation_history"] == [
        {
            "query": "Synthesize robotics researchers and trends in Gujarat",
            "response": result["synthesized_response"],
        }
    ]


def test_workflow_surfaces_rag_failures_as_warnings(monkeypatch):
    _clear_query_cache()
    # Clear executor skill caches so monkeypatch is respected
    executor_module._sql_skill_instance = None
    executor_module._sql_skill_class_id = None
    executor_module._rag_skill_instance = None
    executor_module._rag_skill_class_id = None

    monkeypatch.setattr(executor_module, "RAGSkill", FailingRAGSkill)

    monkeypatch.setattr(graph_module, "log_query", lambda *args, **kwargs: None)
    monkeypatch.setattr(executor_module, "log_sql", lambda *args, **kwargs: None)
    monkeypatch.setattr(synthesizer_module, "log_llm_call", lambda *args, **kwargs: None)
    monkeypatch.setattr(executor_module, "TextToSQLSkill", StubTextToSQLSkill)
    monkeypatch.setattr(executor_module, "RAGSkill", FailingRAGSkill)
    monkeypatch.setattr(synthesizer_module, "get_llm_mesh", lambda: None)
    monkeypatch.setattr(synthesizer_module, "get_local_llm_client", lambda: None)

    workflow = NRGWorkflow()

    result = workflow.run(
        "Synthesize robotics researchers and trends in Gujarat",
        user_tier=1,
        session_id="warning-session-1",
    )

    assert result["warnings"] == [
        {
            "node": "executor",
            "skill": "rag",
            "error_type": "RuntimeError",
            "message": "Qdrant unavailable",
        }
    ]
    assert result["retrieval_sources"] == ["structured"]
    assert result["provenance"]["cloud_synthesis_used"] is False
