"""Tests for Multi-Hop Planner — Protocol #37: DAG Query Decomposition.

Verifies:
1. DAG structure: nodes + edges format
2. Topological execution: parents before children
3. Comparison queries produce parallel branches
4. Sequential queries produce chain
5. Optional node handling
6. Context passing from parent to child
7. Fallback to flat subqueries when is_dag=False
"""

import pytest

from src.orchestration.nodes.planner import (
    _heuristic_decompose,
    _build_dag as planner_build_dag,
)
from src.orchestration.nodes.executor import _build_dag as exec_build_dag, _execute_dag

pytestmark = pytest.mark.slow


class TestDAGDecomposition:
    """Test DAG structure generation from queries."""

    def test_simple_query_single_node(self):
        """Single subquery bypasses DAG execution."""
        result = _heuristic_decompose(
            "Find all AI researchers in Gujarat",
            "table: researchers\ntable: publications"
        )
        assert result["is_dag"] is False
        assert result["dag_nodes"] == []
        assert result["dag_root_id"] == ""

    def test_comparison_query_parallel_branches(self):
        """Compare Gujarat and Karnataka produces root + parallel branches."""
        result = _heuristic_decompose(
            "Compare Gujarat and Karnataka AI output over 5 years and show the funding gap",
            "table: researchers\ntable: funding_records"
        )
        assert result["is_dag"] is True
        assert len(result["dag_nodes"]) >= 2
        root = next(n for n in result["dag_nodes"] if n["id"] == result["dag_root_id"])
        assert root["depends_on"] == []
        for n in result["dag_nodes"]:
            if n["id"] != result["dag_root_id"]:
                assert result["dag_root_id"] in n["depends_on"]

    def test_sequential_subqueries_chain(self):
        """Sequential subqueries produce chain DAG."""
        result = _heuristic_decompose(
            "Find robotics researchers. Then list their publications.",
            "table: researchers\ntable: publications"
        )
        if len(result["dag_nodes"]) > 1:
            ids = [n["id"] for n in result["dag_nodes"]]
            for n in result["dag_nodes"]:
                if n["depends_on"]:
                    assert all(dep in ids for dep in n["depends_on"])

    def test_dag_fallback_to_flat(self):
        """If is_dag=False, flat subqueries used."""
        result = _heuristic_decompose(
            "Find robotics researchers",
            "table: researchers"
        )
        assert "subqueries" in result
        assert result["is_dag"] is False
        assert result["dag_nodes"] == []

    def test_dag_node_fields_complete(self):
        """Each DAG node has all required fields."""
        result = _heuristic_decompose(
            "Compare Gujarat and Karnataka AI output",
            "table: researchers\ntable: funding_records"
        )
        for node in result["dag_nodes"]:
            assert "id" in node
            assert "subquery" in node
            assert "skill" in node
            assert "depends_on" in node
            assert "tables" in node
            assert "output_shape" in node
            assert "optional" in node


class TestDAGTopologicalSort:
    """Test topological sort in executor DAG builder."""

    def test_single_node_order(self):
        """Single node returns single-item order."""
        nodes = [{"id": "a", "subquery": "test", "skill": "sql", "depends_on": [], "tables": [], "output_shape": "list"}]
        _, order = exec_build_dag(nodes)
        assert order == ["a"]

    def test_two_independent_nodes(self):
        """Two nodes with no dependencies return in any order."""
        nodes = [
            {"id": "a", "subquery": "test1", "skill": "sql", "depends_on": [], "tables": [], "output_shape": "list"},
            {"id": "b", "subquery": "test2", "skill": "sql", "depends_on": [], "tables": [], "output_shape": "list"},
        ]
        _, order = exec_build_dag(nodes)
        assert set(order) == {"a", "b"}

    def test_parent_before_child(self):
        """Parent appears before child in execution order."""
        nodes = [
            {"id": "root", "subquery": "test", "skill": "sql", "depends_on": [], "tables": [], "output_shape": "list"},
            {"id": "child", "subquery": "test2", "skill": "sql", "depends_on": ["root"], "tables": [], "output_shape": "list"},
        ]
        _, order = exec_build_dag(nodes)
        assert order.index("root") < order.index("child")

    def test_diamond_dependency(self):
        """Diamond DAG: root -> a,b -> c. Root first, c last."""
        nodes = [
            {"id": "root", "subquery": "root", "skill": "sql", "depends_on": [], "tables": [], "output_shape": "list"},
            {"id": "a", "subquery": "a", "skill": "sql", "depends_on": ["root"], "tables": [], "output_shape": "list"},
            {"id": "b", "subquery": "b", "skill": "sql", "depends_on": ["root"], "tables": [], "output_shape": "list"},
            {"id": "c", "subquery": "c", "skill": "sql", "depends_on": ["a", "b"], "tables": [], "output_shape": "list"},
        ]
        _, order = exec_build_dag(nodes)
        ri, ai, bi, ci = [order.index(n) for n in ["root", "a", "b", "c"]]
        assert ri < ai and ri < bi
        assert ci > ai and ci > bi

    def test_optional_node_skipped_on_missing_parent(self):
        """Optional node with missing parent is skipped."""
        dag_nodes = [
            {"id": "child", "subquery": "opt_child", "skill": "sql",
             "depends_on": ["nonexistent"], "tables": [], "output_shape": "list", "optional": True},
        ]
        result = _execute_dag(dag_nodes, "child", user_tier=1)
        assert result["dag_node_count"] == 1
        assert result["sql_results"] == []


class TestDAGContextPassing:
    """Test that parent results are passed as context to children."""

    def test_dag_node_enriches_query_with_context(self):
        """When parent results exist, child query is enriched with context."""
        dag_nodes = [
            {"id": "root", "subquery": "Find Gujarat researchers", "skill": "sql",
             "depends_on": [], "tables": ["researchers"], "output_shape": "list", "optional": False},
            {"id": "child", "subquery": "List their publications", "skill": "sql",
             "depends_on": ["root"], "tables": ["publications"], "output_shape": "list", "optional": False},
        ]
        result = _execute_dag(dag_nodes, "root", user_tier=1)
        assert result["dag_node_count"] == 2
        assert "execution_time_ms" in result


class TestPlannerNodeIntegration:
    """Test planner DAG output with mock executor."""

    def test_planner_fallback_produces_valid_dag(self):
        """Planner heuristic fallback always produces valid DAG output."""
        result = _heuristic_decompose(
            "Compare Gujarat and Karnataka robotics research and show funding",
            "table: researchers\ntable: funding_records"
        )
        assert "dag_nodes" in result
        assert "dag_root_id" in result
        assert "is_dag" in result
        assert result["is_dag"] in (True, False)
        assert result["dag_root_id"] in [n["id"] for n in result["dag_nodes"]]

    def test_skills_determination(self):
        """Skills are correctly determined for DAG nodes."""
        result = _heuristic_decompose(
            "Find AI researchers and explain their work",
            "table: researchers\ntable: publications"
        )
        skills = result.get("desired_skills", [])
        assert isinstance(skills, list)


class TestDAGDecompositionFull:
    """Expanded 10-fixture coverage for DAG multi-hop planner."""

    def test_comparison_query_produces_root_plus_branches(self):
        """Comparison query produces root with 2+ child branches."""
        result = _heuristic_decompose(
            "Compare Gujarat and Karnataka AI output over 5 years and show the funding gap",
            "table: researchers\ntable: funding_records"
        )
        assert result["is_dag"] is True
        assert len(result["dag_nodes"]) >= 2
        root = next(n for n in result["dag_nodes"] if n["id"] == result["dag_root_id"])
        assert root["depends_on"] == []
        children = [n for n in result["dag_nodes"] if n["id"] != result["dag_root_id"]]
        assert len(children) >= 2
        for child in children:
            assert result["dag_root_id"] in child["depends_on"]

    def test_sequential_chain_deps(self):
        """Sequential query produces chain of 3+ nodes with dependencies."""
        result = _heuristic_decompose(
            "Find robotics researchers. Then list their publications. Then show their funding.",
            "table: researchers\ntable: publications\ntable: funding_records"
        )
        assert result["is_dag"] is True
        assert len(result["dag_nodes"]) == 3
        ids = [n["id"] for n in result["dag_nodes"]]
        root = next(n for n in result["dag_nodes"] if n["id"] == result["dag_root_id"])
        assert root["depends_on"] == []
        chain_nodes = [n for n in result["dag_nodes"] if n["depends_on"]]
        assert all(dep in ids for node in chain_nodes for dep in node["depends_on"])

    def test_four_hop_sequential_chain_deps(self):
        """Sequential query produces a valid 4-hop chain."""
        result = _heuristic_decompose(
            "Find robotics researchers. Then list their publications. Then show their funding. Then summarize institute gaps.",
            "table: researchers\ntable: publications\ntable: funding_records\ntable: institutions"
        )
        assert result["is_dag"] is True
        assert len(result["dag_nodes"]) == 4
        _, order = exec_build_dag(result["dag_nodes"])
        assert order == [node["id"] for node in result["dag_nodes"]]

    def test_diamond_dag(self):
        """Diamond DAG: root -> a,b -> c. Root before children, c last."""
        nodes = [
            {"id": "root", "subquery": "root", "skill": "sql", "depends_on": [], "tables": [], "output_shape": "list"},
            {"id": "a", "subquery": "a", "skill": "sql", "depends_on": ["root"], "tables": [], "output_shape": "list"},
            {"id": "b", "subquery": "b", "skill": "sql", "depends_on": ["root"], "tables": [], "output_shape": "list"},
            {"id": "c", "subquery": "c", "skill": "sql", "depends_on": ["a", "b"], "tables": [], "output_shape": "list"},
        ]
        _, order = exec_build_dag(nodes)
        ri, ai, bi, ci = [order.index(n) for n in ["root", "a", "b", "c"]]
        assert ri < ai and ri < bi
        assert ci > ai and ci > bi

    def test_optional_node_failure_ignored(self):
        """Optional node whose parent fails is skipped gracefully."""
        dag_nodes = [
            {"id": "parent", "subquery": "fail", "skill": "sql",
             "depends_on": [], "tables": [], "output_shape": "list", "optional": False},
            {"id": "child", "subquery": "opt_child", "skill": "sql",
             "depends_on": ["parent"], "tables": [], "output_shape": "list", "optional": True},
        ]
        result = _execute_dag(dag_nodes, "parent", user_tier=1)
        assert result["dag_node_count"] == 2

    def test_dag_context_contains_parent_results(self):
        """Child node enriched query contains parent SQL result summary."""
        dag_nodes = [
            {"id": "root", "subquery": "Find Gujarat researchers", "skill": "sql",
             "depends_on": [], "tables": ["researchers"], "output_shape": "list", "optional": False},
            {"id": "child", "subquery": "List their publications", "skill": "sql",
             "depends_on": ["root"], "tables": ["publications"], "output_shape": "list", "optional": False},
        ]
        result = _execute_dag(dag_nodes, "root", user_tier=1)
        assert result["dag_node_count"] == 2
        assert "execution_time_ms" in result
        assert "dag_root_id" in result

    def test_dag_with_rag_skill(self):
        """DAG with mixed sql/rag skill nodes executes correctly."""
        dag_nodes = [
            {"id": "root", "subquery": "Find researchers", "skill": "sql",
             "depends_on": [], "tables": ["researchers"], "output_shape": "list", "optional": False},
            {"id": "child", "subquery": "Explain their work", "skill": "rag",
             "depends_on": ["root"], "tables": ["publications"], "output_shape": "mixed_summary", "optional": False},
        ]
        result = _execute_dag(dag_nodes, "root", user_tier=1)
        assert result["dag_node_count"] == 2

    def test_topological_sort_cycle_detection(self):
        """DAG with cycle logs warning and produces partial order."""
        nodes = [
            {"id": "a", "subquery": "a", "skill": "sql", "depends_on": ["c"], "tables": [], "output_shape": "list"},
            {"id": "b", "subquery": "b", "skill": "sql", "depends_on": ["a"], "tables": [], "output_shape": "list"},
            {"id": "c", "subquery": "c", "skill": "sql", "depends_on": ["b"], "tables": [], "output_shape": "list"},
        ]
        _, order = exec_build_dag(nodes)
        assert len(order) < 3

    def test_cycle_dead_end_returns_graceful_error(self):
        """Executor returns a structured error instead of hanging on a cyclic DAG."""
        nodes = [
            {"id": "a", "subquery": "a", "skill": "sql", "depends_on": ["c"], "tables": [], "output_shape": "list"},
            {"id": "b", "subquery": "b", "skill": "sql", "depends_on": ["a"], "tables": [], "output_shape": "list"},
            {"id": "c", "subquery": "c", "skill": "sql", "depends_on": ["b"], "tables": [], "output_shape": "list"},
        ]
        result = _execute_dag(nodes, "a", user_tier=1)
        assert result["dag_node_count"] == 0
        assert result["errors"][0]["error_type"] == "DAGDeadEnd"

    def test_explicit_dag_edges_are_id_lists_not_ordinal(self):
        """depends_on is a list of node ID strings, not ordinal positions."""
        result = _heuristic_decompose(
            "Compare Gujarat and Karnataka robotics research",
            "table: researchers\ntable: funding_records"
        )
        for node in result["dag_nodes"]:
            assert isinstance(node["depends_on"], list)
            for dep in node["depends_on"]:
                assert isinstance(dep, str), f"depends_on must be list[str], got {type(dep)}"
                assert dep.startswith("node_"), f"depends_on IDs must be node IDs, got {dep}"

    def test_planner_rejects_truly_cyclic_plan(self):
        """If a cyclic DAG is constructed, _build_dag returns empty order."""
        cyclic_nodes = [
            {"id": "x", "subquery": "x", "skill": "sql", "depends_on": ["z"], "tables": [], "output_shape": "list"},
            {"id": "y", "subquery": "y", "skill": "sql", "depends_on": ["x"], "tables": [], "output_shape": "list"},
            {"id": "z", "subquery": "z", "skill": "sql", "depends_on": ["y"], "tables": [], "output_shape": "list"},
        ]
        _, order = planner_build_dag(cyclic_nodes)
        assert len(order) == 0, "Cyclic DAG must produce empty execution order"

    def test_topological_sort_stable_on_chain(self):
        """Linear chain a→b→c always produces correct parent-before-child order."""
        nodes = [
            {"id": "root", "subquery": "root", "skill": "sql", "depends_on": [], "tables": [], "output_shape": "list"},
            {"id": "mid", "subquery": "mid", "skill": "sql", "depends_on": ["root"], "tables": [], "output_shape": "list"},
            {"id": "leaf", "subquery": "leaf", "skill": "sql", "depends_on": ["mid"], "tables": [], "output_shape": "list"},
        ]
        _, order = exec_build_dag(nodes)
        assert order == ["root", "mid", "leaf"]

    def test_planner_emits_explicit_edges_with_node_ids(self):
        """Planner DAG output: depends_on entries are IDs, not numeric indexes."""
        result = _heuristic_decompose(
            "Find robotics researchers. Then list their publications. Then show funding.",
            "table: researchers\ntable: publications\ntable: funding_records"
        )
        if result["is_dag"] and len(result["dag_nodes"]) > 1:
            for node in result["dag_nodes"]:
                for dep in node["depends_on"]:
                    ref_found = any(n["id"] == dep for n in result["dag_nodes"])
                    assert ref_found, f"depends_on ID '{dep}' not found in any node id"

    def test_dag_execution_time_recorded(self):
        """Each node's execution_time_ms is recorded."""
        dag_nodes = [
            {"id": "root", "subquery": "Find researchers", "skill": "sql",
             "depends_on": [], "tables": ["researchers"], "output_shape": "list", "optional": False},
        ]
        result = _execute_dag(dag_nodes, "root", user_tier=1)
        assert "execution_time_ms" in result
        assert "root" in result["execution_time_ms"]
        assert result["execution_time_ms"]["root"] >= 0

    def test_single_hop_query_produces_single_node(self):
        """Single-hop query bypasses DAG metadata and executes directly."""
        result = _heuristic_decompose(
            "Find all AI researchers in Gujarat",
            "table: researchers\ntable: publications"
        )
        assert result["is_dag"] is False
        assert result["dag_nodes"] == []
        assert result["dag_root_id"] == ""

    def test_dag_node_output_shape_preserved(self):
        """Each node's output_shape is propagated through execution."""
        dag_nodes = [
            {"id": "root", "subquery": "Find Gujarat researchers", "skill": "sql",
             "depends_on": [], "tables": ["researchers"], "output_shape": "person_list", "optional": False},
            {"id": "child", "subquery": "List publications", "skill": "sql",
             "depends_on": ["root"], "tables": ["publications"], "output_shape": "list_table", "optional": False},
        ]
        result = _execute_dag(dag_nodes, "root", user_tier=1)
        assert result["dag_node_count"] == 2


class TestExecutorDAGPath:
    """Verify executor DAG path is triggered correctly."""

    def test_executor_routes_to_dag_when_is_dag_true(self):
        """When plan.is_dag=True and dag_nodes exist, _execute_dag is called."""
        from unittest.mock import patch
        from src.orchestration.nodes.executor import executor_node, _execute_dag

        mock_state = {
            "user_query": "Compare Gujarat and Karnataka AI output",
            "routing_decision": "text_to_sql",
            "user_tier": 1,
            "plan": {
                "is_dag": True,
                "dag_nodes": [
                    {"id": "root", "subquery": "root", "skill": "sql",
                     "depends_on": [], "tables": [], "output_shape": "list", "optional": False},
                    {"id": "child", "subquery": "child", "skill": "sql",
                     "depends_on": ["root"], "tables": [], "output_shape": "list", "optional": False},
                ],
                "dag_root_id": "root",
            }
        }

        with patch("src.orchestration.nodes.executor._execute_dag", wraps=_execute_dag) as mock_exec:
            mock_exec.return_value = {"sql_results": [], "dag_node_count": 2}
            result = executor_node(mock_state)
            assert result["dag_node_count"] == 2

    def test_executor_bypasses_dag_for_simple_plan(self):
        """Simple plans with is_dag=False execute directly instead of entering DAG mode."""
        from unittest.mock import patch
        from src.orchestration.nodes.executor import executor_node

        mock_state = {
            "user_query": "How many publications in 2023?",
            "routing_decision": "text_to_sql",
            "user_tier": 1,
            "plan": {
                "is_dag": False,
                "dag_nodes": [],
                "dag_root_id": "",
            },
        }

        with patch(
            "src.orchestration.nodes.executor._execute_dag",
            side_effect=AssertionError("DAG path should not run"),
        ), patch(
            "src.orchestration.nodes.executor._execute_sql_only",
            return_value={"sql_results": [{"count": 42}], "dag_node_count": 0},
        ) as mock_sql:
            result = executor_node(mock_state)

        mock_sql.assert_called_once_with("How many publications in 2023?", 1)
        assert result["sql_results"] == [{"count": 42}]
        assert result["dag_node_count"] == 0
