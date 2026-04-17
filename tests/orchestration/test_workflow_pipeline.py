from src.orchestration.graph import NRGWorkflow
import src.orchestration.nodes.executor as executor_module


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


def test_workflow_runs_full_orchestration_pipeline(monkeypatch):
    monkeypatch.setattr(executor_module, "TextToSQLSkill", StubTextToSQLSkill)
    monkeypatch.setattr(executor_module, "RAGSkill", StubRAGSkill)

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
    assert result["retrieved_chunks"] == [
        "Robotics research in Gujarat is growing rapidly."
    ]
    assert "Fallback synthesis" in result["synthesized_response"]
    assert result["conversation_history"] == [
        {
            "query": "Synthesize robotics researchers and trends in Gujarat",
            "response": result["synthesized_response"],
        }
    ]
