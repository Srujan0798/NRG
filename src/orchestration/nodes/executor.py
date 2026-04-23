"""Executor node - executes skills based on routing decision with parallel + DAG execution."""

from __future__ import annotations

import atexit
import logging
import sys
import threading
import concurrent.futures
from collections import defaultdict
from typing import Any
from dataclasses import dataclass, field
from datetime import datetime

from src.skills.text_to_sql.skill import TextToSQLSkill
from src.skills.rag.skill import RAGSkill
from src.audit import log_sql
from src.orchestration.state import NRGState, QueryDAG, QueryDAGNode
from src.observability.langfuse_tracer import trace_llm_call

logger = logging.getLogger(__name__)

_sql_skill_instance: TextToSQLSkill | None = None
_sql_skill_class_id: int | None = None
_rag_skill_instance: RAGSkill | None = None
_rag_skill_class_id: int | None = None
_lock = threading.Lock()

_parallel_executor = concurrent.futures.ThreadPoolExecutor(max_workers=4, thread_name_prefix="executor")

def _shutdown_executor():
    """Clean shutdown of executor thread pool."""
    global _parallel_executor
    _parallel_executor.shutdown(wait=False)
    try:
        logger.info("Executor thread pool shut down")
    except ValueError:
        pass

atexit.register(_shutdown_executor)


@dataclass
class ExecutionResult:
    """Container for parallel execution results."""
    sql_results: list = field(default_factory=list)
    sql_query: str | None = None
    retrieved_chunks: list = field(default_factory=list)
    retrieval_metadata: list = field(default_factory=list)
    retrieval_sources: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    execution_time_ms: dict = field(default_factory=dict)


def _get_sql_skill() -> TextToSQLSkill:
    """Get cached TextToSQLSkill instance (thread-safe, auto-invalidates on patch)."""
    global _sql_skill_instance, _sql_skill_class_id
    _TextToSQLSkill = getattr(sys.modules[__name__], "TextToSQLSkill")
    current_id = id(_TextToSQLSkill)
    if _sql_skill_instance is None or _sql_skill_class_id != current_id:
        with _lock:
            if _sql_skill_instance is None or _sql_skill_class_id != current_id:
                _sql_skill_instance = _TextToSQLSkill()
                _sql_skill_class_id = current_id
    return _sql_skill_instance


def _get_rag_skill() -> RAGSkill:
    """Get cached RAGSkill instance (thread-safe, auto-invalidates on patch)."""
    global _rag_skill_instance, _rag_skill_class_id
    _RAGSkill = getattr(sys.modules[__name__], "RAGSkill")
    current_id = id(_RAGSkill)
    if _rag_skill_instance is None or _rag_skill_class_id != current_id:
        with _lock:
            if _rag_skill_instance is None or _rag_skill_class_id != current_id:
                _rag_skill_instance = _RAGSkill()
                _rag_skill_class_id = current_id
    return _rag_skill_instance


def _execute_sql(user_query: str, user_tier: int) -> tuple[dict[str, Any], float]:
    """Execute SQL query and return result with execution time."""
    start = datetime.now()
    result: dict[str, Any] = {
        "sql_results": [],
        "sql_query": None,
        "errors": [],
        "warnings": [],
    }

    sql_skill = None
    try:
        sql_skill = _get_sql_skill()
        sql_response = sql_skill.execute(user_query, user_tier=user_tier)
        result["sql_query"] = sql_response.get("query")
        result["sql_results"] = sql_response.get("results", [])
        try:
            log_sql("executor", sql_response.get("query", ""), {"row_count": sql_response.get("row_count", 0)})
        except Exception:
            pass
    except Exception as exc:
        logger.error("Text-to-SQL execution failed: %s", exc, exc_info=True)
        warning = {"node": "executor", "skill": "text_to_sql", "error_type": type(exc).__name__, "message": str(exc)}
        result["errors"].append(warning)
        result["warnings"].append(warning)
    finally:
        if sql_skill is not None:
            sql_skill.close()

    execution_time = (datetime.now() - start).total_seconds() * 1000
    return result, execution_time


def _execute_rag(user_query: str, user_tier: int) -> tuple[dict[str, Any], float]:
    """Execute RAG retrieval and return result with execution time."""
    start = datetime.now()
    result: dict[str, Any] = {
        "retrieved_chunks": [],
        "retrieval_metadata": [],
        "errors": [],
        "warnings": [],
        "retrieval_sources": [],
    }

    rag_skill = None
    try:
        rag_skill = _get_rag_skill()
        rag_response = rag_skill.retrieve(user_query, user_tier=user_tier, top_k=5)
        chunks = rag_response.get("chunks", [])
        metadata = rag_response.get("metadata", [])
        zipped_chunks = []
        for idx, (chunk, meta) in enumerate(zip(chunks, metadata)):
            if isinstance(chunk, dict):
                zipped_chunks.append(chunk)
            else:
                zipped_chunks.append({
                    "chunk_text": chunk,
                    "chunk_id": meta.get("chunk_id", str(idx)),
                    "publication_id": meta.get("source_id") or meta.get("document_id", f"chunk_{idx}"),
                    "title": meta.get("title", ""),
                    "source_id": meta.get("source_id") or meta.get("document_id", ""),
                })
        result["retrieved_chunks"] = zipped_chunks if zipped_chunks else chunks
        result["retrieval_metadata"] = metadata
        if result["retrieved_chunks"] or result["retrieval_metadata"]:
            result["retrieval_sources"].append("rag")
    except Exception as exc:
        logger.error("RAG retrieval failed: %s", exc, exc_info=True)
        warning = {"node": "executor", "skill": "rag", "error_type": type(exc).__name__, "message": str(exc)}
        result["errors"].append(warning)
        result["warnings"].append(warning)
    finally:
        if rag_skill is not None:
            rag_skill.close()

    execution_time = (datetime.now() - start).total_seconds() * 1000
    return result, execution_time


@trace_llm_call("executor")
def executor_node(state) -> dict:
    """Execute skills based on routing decision with parallel hybrid and DAG execution."""
    if isinstance(state, NRGState):
        user_query = state.user_query
        routing = state.routing_decision or "text_to_sql"
        user_tier = state.user_tier
        plan = getattr(state, "plan", None) or {}
    else:
        user_query = state.get("user_query", "")
        routing = state.get("routing_decision", "text_to_sql")
        user_tier = state.get("user_tier", 1)
        plan = state.get("plan", {})

    if plan.get("is_dag") and plan.get("dag_nodes"):
        return _execute_dag(plan.get("dag_nodes", []), plan.get("dag_root_id", ""), user_tier)

    needs_sql = routing in ("text_to_sql", "text_to_sql+rag")
    needs_rag = routing in ("rag", "text_to_sql+rag")

    if needs_sql and needs_rag:
        return _execute_parallel(user_query, user_tier)
    elif needs_sql:
        return _execute_sql_only(user_query, user_tier)
    elif needs_rag:
        return _execute_rag_only(user_query, user_tier)
    else:
        return {
            "sql_results": [],
            "retrieved_chunks": [],
            "retrieval_metadata": [],
            "errors": [],
            "warnings": [],
            "retrieval_sources": [],
        }


def _execute_parallel(user_query: str, user_tier: int) -> dict:
    """Execute SQL and RAG in parallel for hybrid queries using shared thread pool."""
    sql_future = _parallel_executor.submit(_execute_sql, user_query, user_tier)
    rag_future = _parallel_executor.submit(_execute_rag, user_query, user_tier)

    sql_result, sql_time = sql_future.result()
    rag_result, rag_time = rag_future.result()

    results: dict[str, Any] = {
        "sql_results": sql_result.get("sql_results", []),
        "sql_query": sql_result.get("sql_query"),
        "retrieved_chunks": rag_result.get("retrieved_chunks", []),
        "retrieval_metadata": rag_result.get("retrieval_metadata", []),
        "errors": sql_result.get("errors", []) + rag_result.get("errors", []),
        "warnings": sql_result.get("warnings", []) + rag_result.get("warnings", []),
        "retrieval_sources": [],
    }

    if results["sql_results"]:
        results["retrieval_sources"].append("structured")
    if rag_result.get("retrieval_sources"):
        results["retrieval_sources"].extend(rag_result.get("retrieval_sources"))

    results["execution_time_ms"] = {
        "sql": sql_time,
        "rag": rag_time,
        "total": sql_time + rag_time,
        "parallel_saved_ms": max(sql_time, rag_time) - min(sql_time, rag_time),
    }

    logger.info(
        "Parallel execution completed: SQL=%dms RAG=%dms total=%dms speedup=%dms",
        sql_time,
        rag_time,
        sql_time + rag_time,
        max(sql_time, rag_time) - min(sql_time, rag_time),
    )

    return results


def _execute_sql_only(user_query: str, user_tier: int) -> dict:
    """Execute SQL only."""
    result, exec_time = _execute_sql(user_query, user_tier)

    results: dict[str, Any] = {
        "sql_results": result.get("sql_results", []),
        "sql_query": result.get("sql_query"),
        "retrieved_chunks": [],
        "retrieval_metadata": [],
        "errors": result.get("errors", []),
        "warnings": result.get("warnings", []),
        "retrieval_sources": [],
        "execution_time_ms": {"sql": exec_time, "total": exec_time},
    }

    if results["sql_results"]:
        results["retrieval_sources"].append("structured")

    return results


def _execute_rag_only(user_query: str, user_tier: int) -> dict:
    """Execute RAG only."""
    result, exec_time = _execute_rag(user_query, user_tier)

    return {
        "sql_results": [],
        "sql_query": None,
        "retrieved_chunks": result.get("retrieved_chunks", []),
        "retrieval_metadata": result.get("retrieval_metadata", []),
        "errors": result.get("errors", []),
        "warnings": result.get("warnings", []),
        "retrieval_sources": result.get("retrieval_sources", []),
        "execution_time_ms": {"rag": exec_time, "total": exec_time},
    }


def _build_dag(nodes: list[dict]) -> tuple[dict[str, dict], list[str]]:
    """Build adjacency list and topological order from DAG nodes.
    
    Returns (node_map, execution_order) where execution_order is nodes
    in topological sort (parents before children).
    """
    node_map: dict[str, dict] = {n["id"]: n for n in nodes}
    in_degree: dict[str, int] = {n["id"]: 0 for n in nodes}
    children: dict[str, list[str]] = defaultdict(list)

    for n in nodes:
        for parent_id in n.get("depends_on", []):
            if parent_id in node_map:
                children[parent_id].append(n["id"])
                in_degree[n["id"]] += 1

    queue = [nid for nid, deg in in_degree.items() if deg == 0]
    order = []
    while queue:
        nid = queue.pop(0)
        order.append(nid)
        for child_id in children[nid]:
            in_degree[child_id] -= 1
            if in_degree[child_id] == 0:
                queue.append(child_id)

    return node_map, order


def _execute_dag(dag_nodes: list[dict], root_id: str, user_tier: int) -> dict:
    """Execute DAG nodes in topological order, passing parent results as context."""
    if not dag_nodes:
        return {
            "sql_results": [],
            "retrieved_chunks": [],
            "retrieval_metadata": [],
            "errors": [],
            "warnings": [],
            "retrieval_sources": [],
        }

    node_map, exec_order = _build_dag(dag_nodes)
    results_map: dict[str, dict] = {}
    all_errors: list[dict] = []
    all_warnings: list[dict] = []
    all_sql_results: list = []
    all_chunks: list = []
    dag_execution_times: dict[str, float] = {}

    for node_id in exec_order:
        node = node_map[node_id]
        if node.get("optional") and node_id not in results_map:
            continue

        context_parts = []
        for parent_id in node.get("depends_on", []):
            if parent_id in results_map:
                parent_result = results_map[parent_id]
                context_parts.append(f"[Context from {parent_id}]: ")
                if parent_result.get("sql_results"):
                    context_parts.append(f"SQL results: {len(parent_result['sql_results'])} rows; ")
                if parent_result.get("retrieved_chunks"):
                    context_parts.append(f"RAG chunks: {len(parent_result['retrieved_chunks'])} items; ")

        enriched_query = node["subquery"]
        if context_parts:
            enriched_query = " ".join(context_parts) + "\n\nOriginal query: " + enriched_query

        skill = node.get("skill", "sql")
        t0 = datetime.now()

        try:
            if skill == "rag":
                result, _ = _execute_rag(enriched_query, user_tier)
            else:
                result, _ = _execute_sql(enriched_query, user_tier)
        except Exception as exc:
            logger.warning("DAG node %s failed: %s", node_id, exc)
            if not node.get("optional"):
                all_errors.append({"node": node_id, "error": str(exc)})
            result = {"sql_results": [], "retrieved_chunks": [], "errors": [str(exc)]}

        dag_execution_times[node_id] = (datetime.now() - t0).total_seconds() * 1000
        results_map[node_id] = result

        all_errors.extend(result.get("errors", []))
        all_warnings.extend(result.get("warnings", []))
        all_sql_results.extend(result.get("sql_results", []))
        all_chunks.extend(result.get("retrieved_chunks", []))

    total_time = sum(dag_execution_times.values())

    logger.info(
        "DAG execution completed: %d nodes, %d total ms, %d errors",
        len(exec_order), total_time, len(all_errors)
    )

    return {
        "sql_results": all_sql_results,
        "retrieved_chunks": all_chunks,
        "retrieval_metadata": [],
        "errors": all_errors,
        "warnings": all_warnings,
        "retrieval_sources": list(set(
            src for r in results_map.values() for src in r.get("retrieval_sources", [])
        )),
        "execution_time_ms": {**dag_execution_times, "total": total_time},
        "dag_node_count": len(exec_order),
        "dag_root_id": root_id,
    }
