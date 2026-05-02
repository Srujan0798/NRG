"""Regression tests for orchestration state transitions.

Covers A5-04: the LangGraph workflow must not contain accidental dead-end
states, and DAG dead-ends must return structured warnings instead of crashing.
"""

from langgraph.graph import END


REQUIRED_NODES = {
    "receiver",
    "planner",
    "router",
    "executor",
    "synthesizer",
    "verifier",
}


def _compiled_workflow_graph():
    from src.orchestration.graph import NRGWorkflow

    return NRGWorkflow().graph


def _drawable_graph():
    return _compiled_workflow_graph().get_graph()


def test_compiled_workflow_has_required_nodes():
    graph = _compiled_workflow_graph()

    actual_nodes = set(graph.nodes)

    assert REQUIRED_NODES <= actual_nodes


def test_workflow_has_expected_linear_edges():
    graph = _drawable_graph()
    edges = {(edge.source, edge.target) for edge in graph.edges}

    assert ("__start__", "receiver") in edges
    assert ("receiver", "planner") in edges
    assert ("planner", "router") in edges
    assert ("router", "executor") in edges
    assert ("executor", "synthesizer") in edges
    assert ("synthesizer", "verifier") in edges


def test_verifier_has_retry_and_end_edges():
    graph = _drawable_graph()
    verifier_edges = {
        (edge.target, edge.data)
        for edge in graph.edges
        if edge.source == "verifier"
    }

    assert ("synthesizer", "retry_synthesis") in verifier_edges
    assert (END, "end_retry") in verifier_edges


def test_no_required_workflow_node_is_a_dead_end():
    graph = _drawable_graph()
    outgoing = {node: set() for node in REQUIRED_NODES}
    for edge in graph.edges:
        if edge.source in outgoing:
            outgoing[edge.source].add(edge.target)

    dead_ends = {node for node, targets in outgoing.items() if not targets}

    assert not dead_ends


def test_dag_cycle_returns_structured_dead_end_error():
    from src.orchestration.nodes.executor import _execute_dag

    result = _execute_dag(
        [
            {
                "id": "a",
                "subquery": "first",
                "skill": "sql",
                "depends_on": ["b"],
            },
            {
                "id": "b",
                "subquery": "second",
                "skill": "rag",
                "depends_on": ["a"],
            },
        ],
        root_id="a",
        user_tier=1,
    )

    assert result["errors"][0]["error_type"] == "DAGDeadEnd"
    assert result["warnings"][0]["error_type"] == "DAGDeadEnd"
    assert result["dag_root_id"] == "a"


def test_verifier_failure_result_retries_once_then_fails():
    from src.orchestration.nodes.verifier import _failure_result

    first = _failure_result(
        retries=0,
        unsupported_claims=["unsupported claim"],
        response="answer",
        faithfulness_score=0.5,
        score_breakdown={},
    )
    second = _failure_result(
        retries=1,
        unsupported_claims=["unsupported claim"],
        response="answer",
        faithfulness_score=0.5,
        score_breakdown={},
    )

    assert first["verification_status"] == "retry"
    assert first["verification_retries"] == 1
    assert second["verification_status"] == "fail"
    assert second["verification_retries"] == 1
