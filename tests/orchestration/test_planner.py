"""Tests for planner node with mocked LLM client."""

import pytest
from unittest.mock import patch, MagicMock
from src.orchestration.nodes.planner import (
    planner_node,
    _parse_plan,
    _state_get,
    _client_model_name,
)


class TestPlannerNode:
    def test_returns_fallback_when_no_client(self):
        with patch("src.orchestration.nodes.planner._get_planner_client", return_value=None):
            result = planner_node({"user_query": "test", "conversation_history": []})
            assert result["plan"] is None
            assert result["planner_metadata"]["mode"] == "heuristic_fallback"

    def test_returns_plan_from_llm(self):
        mock_client = MagicMock()
        mock_client.generate.return_value = '{"subqueries": ["q1"], "schema_tables": ["t1"], "desired_skills": ["sql"], "expected_output_shape": "table"}'
        with patch("src.orchestration.nodes.planner._get_planner_client", return_value=mock_client):
            with patch("src.orchestration.nodes.planner.log_plan"):
                with patch("src.orchestration.nodes.planner.log_llm_call"):
                    result = planner_node({"user_query": "test", "conversation_history": []})
                    assert result["plan"] is not None
                    assert result["plan"]["subqueries"] == ["q1"]
                    assert result["planner_metadata"]["mode"] == "llm"

    def test_fallback_on_llm_error(self):
        mock_client = MagicMock()
        mock_client.generate.side_effect = RuntimeError("LLM unavailable")
        with patch("src.orchestration.nodes.planner._get_planner_client", return_value=mock_client):
            result = planner_node({"user_query": "test", "conversation_history": []})
            assert result["plan"] is None
            assert result["planner_metadata"]["mode"] == "heuristic_fallback"

    def test_state_get_dict(self):
        assert _state_get({"key": "val"}, "key") == "val"
        assert _state_get({"key": "val"}, "missing", "default") == "default"

    def test_state_get_object(self):
        class Obj:
            key = "val"
        assert _state_get(Obj(), "key") == "val"

    def test_parse_plan_valid_json(self):
        plan = _parse_plan('{"subqueries": ["q1"], "schema_tables": [], "desired_skills": [], "expected_output_shape": ""}')
        assert plan.subqueries == ["q1"]

    def test_parse_plan_json_in_text(self):
        plan = _parse_plan('Here is the plan: {"subqueries": ["q1"], "schema_tables": [], "desired_skills": [], "expected_output_shape": ""}')
        assert plan.subqueries == ["q1"]

    def test_parse_plan_invalid_raises(self):
        with pytest.raises(Exception):
            _parse_plan("not json at all")

    def test_client_model_name_from_settings(self):
        client = MagicMock()
        del client.model
        client.settings = MagicMock()
        client.settings.model = "gpt-4o"
        assert _client_model_name(client) == "gpt-4o"

    def test_client_model_name_unknown(self):
        client = MagicMock()
        del client.model
        del client.settings
        assert _client_model_name(client) == "unknown"
