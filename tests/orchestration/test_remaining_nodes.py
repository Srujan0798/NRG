"""Tests for remaining orchestration nodes: receiver, retry_handler, reflector."""

import pytest
from src.orchestration.nodes.receiver import receiver_node, create_initial_state
from src.orchestration.nodes.retry_handler import RetryHandler
from src.orchestration.nodes.reflector import ReflectorNode


class TestReceiverNode:
    """Tests for receiver_node."""

    def test_receiver_with_empty_state(self):
        result = receiver_node({})
        assert "query_id" in result
        assert "session_id" in result
        assert result["user_query"] == ""
        assert result["user_tier"] == 1

    def test_receiver_with_dict_state(self):
        state = {
            "query_id": "q1",
            "session_id": "s1",
            "user_query": "test query",
            "user_tier": 2,
            "conversation_history": [{"query": "old", "response": "answer"}],
        }
        result = receiver_node(state)
        assert result["query_id"] == "q1"
        assert result["session_id"] == "s1"
        assert result["user_query"] == "test query"
        assert result["user_tier"] == 2
        assert len(result["conversation_history"]) == 1

    def test_receiver_generates_uuid_when_missing(self):
        result = receiver_node({})
        assert len(result["query_id"]) == 36
        assert result["query_id"] == result["session_id"]

    def test_receiver_handles_none_values(self):
        state = {
            "query_id": None,
            "session_id": None,
            "user_tier": None,
        }
        result = receiver_node(state)
        assert "query_id" in result
        assert "session_id" in result

    def test_create_initial_state(self):
        result = create_initial_state("my query", user_tier=3, session_id="custom-session")
        assert result["user_query"] == "my query"
        assert result["user_tier"] == 3
        assert result["session_id"] == "custom-session"
        assert result["conversation_history"] == []
        assert "query_id" in result

    def test_create_initial_state_defaults(self):
        result = create_initial_state("query")
        assert result["user_tier"] == 1
        assert result["session_id"] == result["query_id"]
        assert result["conversation_history"] == []


class TestRetryHandler:
    """Tests for RetryHandler."""

    def test_successful_operation_no_retry(self):
        handler = RetryHandler(max_retries=3)
        call_count = 0

        def successful_op():
            nonlocal call_count
            call_count += 1
            return "success"

        result = handler.handle_retry(successful_op)
        assert result == "success"
        assert call_count == 1

    def test_retry_on_failure_then_success(self):
        handler = RetryHandler(max_retries=3)
        call_count = 0

        def flaky_op():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("temporary failure")
            return "recovered"

        result = handler.handle_retry(flaky_op)
        assert result == "recovered"
        assert call_count == 3

    def test_max_retries_exhausted(self):
        handler = RetryHandler(max_retries=3)

        def always_fails():
            raise ValueError("always fails")

        with pytest.raises(ValueError, match="always fails"):
            handler.handle_retry(always_fails)

    def test_retry_with_args(self):
        handler = RetryHandler(max_retries=2)

        def add(a, b):
            return a + b

        result = handler.handle_retry(add, 2, 3)
        assert result == 5

    def test_retry_with_kwargs(self):
        handler = RetryHandler(max_retries=2)

        def greet(name, greeting="hello"):
            return f"{greeting}, {name}"

        result = handler.handle_retry(greet, "world", greeting="hi")
        assert result == "hi, world"


class TestReflectorNode:
    """Tests for ReflectorNode."""

    def test_validate_complete_output(self):
        reflector = ReflectorNode()
        output = {
            "query_intent": "search",
            "results": [{"id": 1}],
            "confidence_score": 0.9,
            "execution_time": 5.0,
        }
        assert reflector.validate_output_completeness(output) is True

    def test_validate_missing_required_field(self):
        reflector = ReflectorNode()
        output = {
            "query_intent": "search",
            "results": [],
            "confidence_score": 0.9,
        }
        assert reflector.validate_output_completeness(output) is False

    def test_validate_insufficient_results(self):
        reflector = ReflectorNode()
        output = {
            "query_intent": "search",
            "results": [],
            "confidence_score": 0.9,
            "execution_time": 1.0,
        }
        assert reflector.validate_output_completeness(output) is False

    def test_validate_execution_time_exceeded(self):
        reflector = ReflectorNode()
        output = {
            "query_intent": "search",
            "results": [{"id": 1}],
            "confidence_score": 0.9,
            "execution_time": 35.0,
        }
        assert reflector.validate_output_completeness(output) is False

    def test_validate_with_min_results(self):
        reflector = ReflectorNode()
        output = {
            "query_intent": "search",
            "results": [1],
            "confidence_score": 0.5,
            "execution_time": 1.0,
        }
        assert reflector.validate_output_completeness(output) is True

    def test_reflector_default_rules(self):
        reflector = ReflectorNode()
        assert "required_fields" in reflector.validation_rules
        assert reflector.validation_rules["min_results"] == 1
        assert reflector.validation_rules["max_execution_time"] == 30.0
