"""Executor node - executes skills based on routing decision."""

import logging
import threading
from typing import Any

from src.skills.text_to_sql.skill import TextToSQLSkill
from src.skills.rag.skill import RAGSkill
from src.audit import log_sql
from src.orchestration.state import NRGState

logger = logging.getLogger(__name__)

# Module-level skill caches with lazy initialization for efficiency.
# Skills are expensive to instantiate (model loading, DB connection setup).
# Cache invalidates automatically when the class is monkeypatched (tests).
_sql_skill_instance: TextToSQLSkill | None = None
_sql_skill_class_id: int | None = None
_rag_skill_instance: RAGSkill | None = None
_rag_skill_class_id: int | None = None
_lock = threading.Lock()


def _get_sql_skill() -> TextToSQLSkill:
    """Get cached TextToSQLSkill instance (thread-safe, auto-invalidates on patch)."""
    global _sql_skill_instance, _sql_skill_class_id
    current_id = id(TextToSQLSkill)
    if _sql_skill_instance is None or _sql_skill_class_id != current_id:
        with _lock:
            if _sql_skill_instance is None or _sql_skill_class_id != current_id:
                _sql_skill_instance = TextToSQLSkill()
                _sql_skill_class_id = current_id
    return _sql_skill_instance


def _get_rag_skill() -> RAGSkill:
    """Get cached RAGSkill instance (thread-safe, auto-invalidates on patch)."""
    global _rag_skill_instance, _rag_skill_class_id
    current_id = id(RAGSkill)
    if _rag_skill_instance is None or _rag_skill_class_id != current_id:
        with _lock:
            if _rag_skill_instance is None or _rag_skill_class_id != current_id:
                _rag_skill_instance = RAGSkill()
                _rag_skill_class_id = current_id
    return _rag_skill_instance


def executor_node(state) -> dict:
    """Execute skills based on routing decision."""
    if isinstance(state, NRGState):
        user_query = state.user_query
        routing = state.routing_decision or "text_to_sql"
        user_tier = state.user_tier
    else:
        user_query = state.get("user_query", "")
        routing = state.get("routing_decision", "text_to_sql")
        user_tier = state.get("user_tier", 1)

    results: dict[str, Any] = {
        "sql_results": [],
        "retrieved_chunks": [],
        "retrieval_metadata": [],
        "errors": [],
        "warnings": [],
        "retrieval_sources": [],
    }

    if routing in ("text_to_sql", "text_to_sql+rag"):
        sql_skill = None
        try:
            sql_skill = _get_sql_skill()
            sql_result = sql_skill.execute(user_query, user_tier=user_tier)
            results["sql_query"] = sql_result.get("query")
            results["sql_results"] = sql_result.get("results", [])
            if results["sql_results"]:
                results["retrieval_sources"].append("structured")

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
            warning = {
                "node": "executor",
                "skill": "text_to_sql",
                "error_type": type(exc).__name__,
                "message": str(exc),
            }
            results["errors"].append(warning)
            results["warnings"].append(warning)
        finally:
            if sql_skill is not None:
                sql_skill.close()

    if routing in ("rag", "text_to_sql+rag"):
        rag_skill = None
        try:
            rag_skill = _get_rag_skill()
            rag_result = rag_skill.retrieve(user_query, user_tier=user_tier, top_k=5)
            results["retrieved_chunks"] = rag_result.get("chunks", [])
            results["retrieval_metadata"] = rag_result.get("metadata", [])
            if results["retrieved_chunks"] or results["retrieval_metadata"]:
                results["retrieval_sources"].append("rag")
        except Exception as exc:
            logger.error("RAG retrieval failed: %s", exc, exc_info=True)
            warning = {
                "node": "executor",
                "skill": "rag",
                "error_type": type(exc).__name__,
                "message": str(exc),
            }
            results["errors"].append(warning)
            results["warnings"].append(warning)
        finally:
            if rag_skill is not None:
                rag_skill.close()

    return results
