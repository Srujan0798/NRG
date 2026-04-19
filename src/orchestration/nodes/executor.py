"""Executor node - executes skills based on routing decision."""

import logging
from typing import Dict, Any

from src.skills.text_to_sql.skill import TextToSQLSkill
from src.skills.rag.skill import RAGSkill
from src.audit import log_sql
from src.orchestration.state import NRGState

logger = logging.getLogger(__name__)


def executor_node(state) -> dict:
    """Execute skills based on routing decision."""
    # Handle both NRGState dataclass and dict
    if isinstance(state, NRGState):
        user_query = state.user_query
        routing = state.routing_decision or "text_to_sql"
        user_tier = state.user_tier
    else:
        user_query = state.get("user_query", "")
        routing = state.get("routing_decision", "text_to_sql")
        user_tier = state.get("user_tier", 1)

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
            
            # Audit: log SQL execution with HMAC chain
            try:
                log_sql(
                    "executor",
                    sql_result.get("query", ""),
                    {"row_count": sql_result.get("row_count", 0)},
                )
            except Exception:
                logger.warning("Audit log_sql failed", exc_info=True)
                
        except Exception as exc:
            logger.error("Text-to-SQL execution failed: %s", exc, exc_info=True)
            results["errors"].append({
                "node": "executor",
                "skill": "text_to_sql",
                "error_type": type(exc).__name__,
                "error": str(exc)
            })
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
            logger.error("RAG retrieval failed: %s", exc, exc_info=True)
            results["errors"].append({
                "node": "executor",
                "skill": "rag",
                "error_type": type(exc).__name__,
                "error": str(exc)
            })
        finally:
            if rag_skill is not None:
                rag_skill.close()

    return results
