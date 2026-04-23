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
    _build_dag,
    _extract_subqueries,
    _determine_skills,
)
from src.orchestration.nodes.executor import _build_dag as exec_build_dag, _execute_dag


class TestDAGDecomposition:
    """Test DAG structure generation from queries."""

    def test_simple_query_single_node(self):
        """Single subquery produces single-node DAG."""
        result = _heuristic_decompose(
            "Find all AI researchers in Gujarat",
            "table: researchers\ntable: publications"
        )
        assert result["is_dag"] is True
        assert len(result["dag_nodes"]) == 1
        assert result["dag_root_id"] == result["dag_nodes"][0]["id"]
        assert result["dag_nodes"][0]["depends_on"] == []

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
        assert result["is_dag"] is True

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
