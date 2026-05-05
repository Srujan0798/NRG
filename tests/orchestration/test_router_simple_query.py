"""Tests for simple query bypass — simple queries route directly without multi-hop planner.

Covers A5-07: Query planner over-classification — simple queries should bypass multi-hop.
"""

from src.orchestration.nodes.router import router_node


class TestSimpleQueryBypass:
    """Simple queries (0-hop) should route to direct SQL execution, not multi-hop."""

    def test_count_query_routes_to_text_to_sql(self):
        """'How many X' queries are clearly structured, not multi-hop."""
        state = {
            "user_query": "How many publications does IIT Bombay have?",
            "user_tier": 1,
            "plan": {},
            "conversation_history": [],
        }
        result = router_node(state)
        assert result["routing_decision"] == "text_to_sql"
        assert result["plan_skills_used"] is False

    def test_existence_query_routes_to_text_to_sql(self):
        """'Does X have Y' queries are structured SQL, not multi-hop."""
        state = {
            "user_query": "Does any researcher at IIT Delhi work on quantum computing?",
            "user_tier": 1,
            "plan": {},
            "conversation_history": [],
        }
        result = router_node(state)
        assert result["routing_decision"] == "text_to_sql"

    def test_aggregation_query_routes_to_text_to_sql(self):
        """Top-N aggregation queries are structured SQL."""
        state = {
            "user_query": "List top 10 funding agencies by total grant amount",
            "user_tier": 1,
            "plan": {},
            "conversation_history": [],
        }
        result = router_node(state)
        assert result["routing_decision"] == "text_to_sql"

    def test_filter_query_routes_to_text_to_sql(self):
        """Filtered queries with known entities are structured SQL."""
        state = {
            "user_query": "Show me all robotics researchers in Gujarat",
            "user_tier": 1,
            "plan": {},
            "conversation_history": [],
        }
        result = router_node(state)
        assert result["routing_decision"] in ("text_to_sql", "text_to_sql+rag")

    def test_multi_word_but_simple_query_not_routed_to_multihop(self):
        """Simple multi-word queries still route to text_to_sql, not multi-hop planner."""
        state = {
            "user_query": "What is the total funding for renewable energy research?",
            "user_tier": 1,
            "plan": {},
            "conversation_history": [],
        }
        result = router_node(state)
        assert result["routing_decision"] not in ("text_to_sql+rag+planner", "text_to_sql+rag+planner+execution")
        assert result["plan_skills_used"] is False

    def test_single_word_query_defaults_to_rag(self):
        """Single-word queries are ambiguous — defaulting to RAG is acceptable."""
        state = {
            "user_query": "robotics",
            "user_tier": 1,
            "plan": {},
            "conversation_history": [],
        }
        result = router_node(state)
        assert result["intent"] == "unstructured"
        assert result["routing_decision"] == "rag"

    def test_empty_query_defaults_to_hybrid(self):
        """Empty queries are edge cases — defaulting to hybrid is acceptable."""
        state = {
            "user_query": "",
            "user_tier": 1,
            "plan": {},
            "conversation_history": [],
        }
        result = router_node(state)
        assert result["intent"] == "hybrid"
        assert result["stage"] == "edge_case"

    def test_sql_injection_is_rejected(self):
        """SQL injection patterns route to hybrid for security review."""
        state = {
            "user_query": "'; DROP TABLE researchers; --",
            "user_tier": 1,
            "plan": {},
            "conversation_history": [],
        }
        result = router_node(state)
        assert result["stage"] == "security"
        assert result["is_ambiguous"] is True
