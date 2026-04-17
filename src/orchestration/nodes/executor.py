"""Executor Node - Execute skills and retrieve data."""

import logging
from typing import TypedDict
from typing_extensions import NotRequired

from src.skills.rag.skill import RAGSkill
from src.skills.text_to_sql.skill import TextToSQLSkill


logger = logging.getLogger(__name__)


class ExecutorState(TypedDict):
    """State passed from executor node."""

    sql_query: NotRequired[str]
    sql_results: list
    retrieved_chunks: list
    retrieval_metadata: list
    errors: list


def executor_node(state):
    """Execute skills based on routing decision."""
    # Extract routing decision from state object
    if hasattr(state, "routing_decision"):
        routing = state.routing_decision
    elif isinstance(state, dict):
        routing = state.get("routing_decision", "rag")
    else:
        routing = "rag"

    if hasattr(state, "user_query"):
        user_query = state.user_query
    elif isinstance(state, dict):
        user_query = state.get("user_query", "")
    else:
        user_query = ""

    if hasattr(state, "user_tier"):
        user_tier = state.user_tier
    elif isinstance(state, dict):
        user_tier = state.get("user_tier", 1)
    else:
        user_tier = 1

    results = {
        "sql_results": [],
        "retrieved_chunks": [],
        "retrieval_metadata": [],
        "errors": [],
    }

    if routing in ("text_to_sql", "text_to_sql+rag"):
        sql_skill = None
        try:
            sql_skill = TextToSQLSkill()
            sql_result = sql_skill.execute(user_query, user_tier=user_tier)
            results["sql_query"] = sql_result.get("query")
            results["sql_results"] = sql_result.get("results", [])
        except Exception as exc:
            logger.warning("Text-to-SQL execution failed: %s", exc)
            results["errors"].append({"node": "executor", "error": str(exc)})
        finally:
            if sql_skill is not None:
                sql_skill.close()

    if routing in ("rag", "text_to_sql+rag"):
        rag_skill = None
        try:
            rag_skill = RAGSkill()
            rag_result = rag_skill.retrieve(user_query, user_tier=user_tier, top_k=5)
            results["retrieved_chunks"] = rag_result.get("chunks", [])
            results["retrieval_metadata"] = rag_result.get("metadata", [])
        except Exception as exc:
            logger.warning("RAG retrieval failed: %s", exc)
            results["errors"].append({"node": "executor", "error": str(exc)})
        finally:
            if rag_skill is not None:
                rag_skill.close()

    return results
