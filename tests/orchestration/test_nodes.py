"""Tests for orchestration receiver, router, executor, and state nodes."""

from unittest.mock import patch, MagicMock
from src.orchestration.state import NRGState


class TestNRGState:
    def test_default_construction(self):
        state = NRGState(user_query="test")
        assert state.user_query == "test"
        assert state.conversation_history == []
        assert state.user_tier == 1

    def test_with_all_fields(self):
        state = NRGState(
            user_query="query",
            conversation_history=[{"query": "q", "response": "r"}],
            user_tier=2,
            query_id="user1",
            session_id="s1",
        )
        assert state.user_tier == 2
        assert state.session_id == "s1"

    def test_add_trace(self):
        state = NRGState(user_query="test")
        state.add_trace("planner", "started", {"key": "val"})
        assert len(state.trace) == 1
        assert state.trace[0]["node"] == "planner"

    def test_add_error(self):
        state = NRGState(user_query="test")
        state.add_error("executor", "something failed")
        assert len(state.errors) == 1
        assert state.errors[0]["node"] == "executor"

    def test_to_dict(self):
        state = NRGState(user_query="test")
        d = state.to_dict()
        assert isinstance(d, dict)
        assert d["user_query"] == "test"

    def test_from_dict(self):
        state = NRGState.from_dict({"user_query": "hello"})
        assert state.user_query == "hello"

    def test_to_json_and_back(self):
        state = NRGState(user_query="test", user_tier=3)
        json_str = state.to_json()
        restored = NRGState.from_json(json_str)
        assert restored.user_query == "test"
        assert restored.user_tier == 3


class TestReceiverNode:
    def test_receiver_creates_state(self):
        from src.orchestration.nodes.receiver import receiver_node
        result = receiver_node({"user_query": "test query", "user_tier": 2, "session_id": "s1"})
        assert result["user_query"] == "test query"
        assert result.get("session_id") == "s1"
        assert "query_id" in result
        assert "created_at" in result

    def test_receiver_generates_query_id(self):
        from src.orchestration.nodes.receiver import receiver_node
        result = receiver_node({"user_query": "hello"})
        assert result["query_id"]
        assert len(result["query_id"]) > 0

    def test_receiver_default_tier(self):
        from src.orchestration.nodes.receiver import receiver_node
        result = receiver_node({"user_query": "hello"})
        assert result["user_tier"] == 1


class TestRouterNode:
    def test_router_routes_text_to_sql(self):
        from src.orchestration.nodes.router import router_node
        result = router_node({"user_query": "How many researchers are in Gujarat?", "plan": {"desired_skills": ["sql"]}})
        assert result["routing_decision"] == "text_to_sql"

    def test_router_routes_rag(self):
        from src.orchestration.nodes.router import router_node
        result = router_node({"user_query": "Tell me about AI research trends", "plan": {"desired_skills": ["rag"]}})
        assert result["routing_decision"] == "rag"

    def test_router_hybrid(self):
        from src.orchestration.nodes.router import router_node
        result = router_node({"user_query": "List and explain AI research", "plan": {"desired_skills": ["sql", "rag"]}})
        assert result["routing_decision"] == "text_to_sql+rag"

    def test_router_no_plan(self):
        from src.orchestration.nodes.router import router_node
        result = router_node({"user_query": "test", "plan": None})
        assert "routing_decision" in result
        assert "intent" in result

    def test_router_ambiguous_best(self):
        from src.orchestration.nodes.router import router_node
        result = router_node({"user_query": "Who is the best researcher in AI?"})
        assert result["is_ambiguous"] is True
        assert any("best" in c for c in result.get("clarifications", []))
        assert result["intent"] == "hybrid"

    def test_router_ambiguous_compare(self):
        from src.orchestration.nodes.router import router_node
        result = router_node({"user_query": "Compare IIT Bombay and IISc"})
        assert result["is_ambiguous"] is True
        assert any("compare" in c for c in result.get("clarifications", []))

    def test_router_not_ambiguous(self):
        from src.orchestration.nodes.router import router_node
        result = router_node({"user_query": "List researchers in Gujarat"})
        assert result["is_ambiguous"] is False
        assert result["intent"] == "structured"


class TestExecutorNode:
    @patch("src.orchestration.nodes.executor.RAGSkill")
    @patch("src.orchestration.nodes.executor.TextToSQLSkill")
    @patch("src.orchestration.nodes.executor.log_sql")
    def test_executor_sql_route(self, mock_log_sql, mock_sql_cls, mock_rag_cls):
        from src.orchestration.nodes.executor import executor_node
        mock_sql = MagicMock()
        mock_sql.execute.return_value = {
            "query": "SELECT COUNT(*) FROM researchers",
            "results": [{"count": 5}],
            "row_count": 1,
        }
        mock_sql.close = MagicMock()
        mock_sql_cls.return_value = mock_sql

        result = executor_node({
            "routing_decision": "text_to_sql",
            "user_query": "count researchers",
            "user_tier": 1,
            "plan": {"subqueries": ["SELECT COUNT(*) FROM researchers"]},
        })
        assert len(result["sql_results"]) > 0
        assert result["sql_query"] == "SELECT COUNT(*) FROM researchers"
        mock_sql.close.assert_not_called()

    @patch("src.orchestration.nodes.executor.RAGSkill")
    @patch("src.orchestration.nodes.executor.TextToSQLSkill")
    def test_executor_rag_route(self, mock_sql_cls, mock_rag_cls):
        from src.orchestration.nodes.executor import executor_node
        mock_rag = MagicMock()
        mock_rag.retrieve.return_value = {
            "chunks": ["AI research in India..."],
            "metadata": [{"source_id": "pub1"}],
        }
        mock_rag.close = MagicMock()
        mock_rag_cls.return_value = mock_rag

        result = executor_node({
            "routing_decision": "rag",
            "user_query": "AI research",
            "user_tier": 1,
            "plan": {},
        })
        assert len(result["retrieved_chunks"]) > 0
        mock_rag.close.assert_not_called()

    @patch("src.orchestration.nodes.executor.RAGSkill")
    @patch("src.orchestration.nodes.executor.TextToSQLSkill")
    def test_executor_sql_failure_graceful(self, mock_sql_cls, mock_rag_cls):
        from src.orchestration.nodes.executor import executor_node
        mock_sql = MagicMock()
        mock_sql.execute.side_effect = RuntimeError("DB down")
        mock_sql.close = MagicMock()
        mock_sql_cls.return_value = mock_sql

        result = executor_node({
            "routing_decision": "text_to_sql",
            "user_query": "count",
            "user_tier": 1,
            "plan": {},
        })
        assert len(result["errors"]) > 0
        mock_sql.close.assert_not_called()

    @patch("src.orchestration.nodes.executor.RAGSkill")
    @patch("src.orchestration.nodes.executor.TextToSQLSkill")
    def test_executor_hybrid_route(self, mock_sql_cls, mock_rag_cls):
        from src.orchestration.nodes.executor import executor_node
        mock_sql = MagicMock()
        mock_sql.execute.return_value = {"query": "SELECT 1", "results": [{"n": 1}], "row_count": 1}
        mock_sql.close = MagicMock()
        mock_sql_cls.return_value = mock_sql

        mock_rag = MagicMock()
        mock_rag.retrieve.return_value = {"chunks": ["info"], "metadata": []}
        mock_rag.close = MagicMock()
        mock_rag_cls.return_value = mock_rag

        result = executor_node({
            "routing_decision": "text_to_sql+rag",
            "user_query": "list and explain",
            "user_tier": 1,
            "plan": {},
        })
        assert len(result["sql_results"]) > 0
        assert len(result["retrieved_chunks"]) > 0
        mock_sql.close.assert_not_called()
        mock_rag.close.assert_not_called()
