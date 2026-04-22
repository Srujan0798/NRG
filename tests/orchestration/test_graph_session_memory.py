from src.orchestration.graph import NRGWorkflow
from src.caching.redis_layer import _get_redis


class FakeCompiledGraph:
    def __init__(self):
        self.invocations = []

    def invoke(self, state, config):
        self.invocations.append({"state": dict(state), "config": dict(config)})
        return {
            **state,
            "intent": "structured",
            "routing_decision": "text_to_sql",
            "synthesized_response": f"response for: {state['user_query']}",
            "verification_status": True,
        }


def test_workflow_reuses_session_id_and_passes_prior_turns():
    # Clear any cached query results from Redis so graph.invoke is actually called
    redis_client = _get_redis()
    if redis_client:
        for key in redis_client.scan_iter(match="query:*"):
            redis_client.delete(key)

    workflow = NRGWorkflow()
    fake_graph = FakeCompiledGraph()
    workflow.graph = fake_graph

    first_result = workflow.run(
        "Find robotics researchers in Gujarat",
        user_tier=1,
        session_id="session-1",
    )
    second_result = workflow.run(
        "What funding do they have?",
        user_tier=1,
        session_id="session-1",
    )

    assert first_result["session_id"] == "session-1"
    assert second_result["session_id"] == "session-1"
    assert fake_graph.invocations[0]["config"]["configurable"]["thread_id"] == "session-1"
    assert fake_graph.invocations[1]["config"]["configurable"]["thread_id"] == "session-1"
    assert fake_graph.invocations[1]["state"]["conversation_history"] == [
        {
            "query": "Find robotics researchers in Gujarat",
            "response": "response for: Find robotics researchers in Gujarat",
        }
    ]
