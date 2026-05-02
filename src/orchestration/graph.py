"""LangGraph orchestration for the Phase 1 NRG query workflow."""

from __future__ import annotations

import json
import logging
import os
import time
import uuid
from collections.abc import Callable, Mapping
from functools import wraps
from pathlib import Path
from typing import Any, cast

from dotenv import load_dotenv
from langgraph.graph import END, StateGraph

from src.audit import log_query
from src.caching.redis_layer import cache_query
from src.orchestration.nodes.executor import executor_node
from src.orchestration.nodes.receiver import create_initial_state, receiver_node
from src.orchestration.nodes.router import router_node
from src.orchestration.nodes.synthesizer import synthesizer_node
from src.orchestration.state import NRGState

JSONDict = dict[str, Any]
NodeFn = Callable[[Any], Any]


def _as_json_dict(value: Any) -> JSONDict:
    if not isinstance(value, Mapping):
        return {}
    return dict(cast(Mapping[str, Any], value))


def _float_dict(value: Any) -> dict[str, float]:
    result: dict[str, float] = {}
    for key, raw_value in _as_json_dict(value).items():
        if isinstance(raw_value, (int, float)) and not isinstance(raw_value, bool):
            result[key] = float(raw_value)
    return result


def _node_timings_from_state(state: Any) -> dict[str, float]:
    if isinstance(state, Mapping):
        return _float_dict(cast(Mapping[str, Any], state).get("node_timings", {}))
    raw_timings = getattr(state, "node_timings", {})
    return _float_dict(raw_timings)


def _assign_node_timings(state: Any, node_timings: dict[str, float]) -> None:
    if isinstance(state, dict):
        state["node_timings"] = node_timings
    elif hasattr(state, "node_timings"):
        state.node_timings = node_timings


try:
    from src.orchestration.nodes.planner import planner_node
except ModuleNotFoundError:

    def planner_node(state: Any) -> JSONDict:
        """Phase 1 fallback planner.

        The experimental cloud planner is quarantined until it is wired through
        the evidence/egress policy. Router heuristics remain the active path.
        """
        return {"plan": None}


try:
    from src.orchestration.nodes.verifier import verifier_node
except ModuleNotFoundError:

    def verifier_node(state: Any) -> JSONDict:
        """Phase 1 fallback verifier."""
        if isinstance(state, Mapping):
            response = cast(Mapping[str, Any], state).get("synthesized_response")
        else:
            response = getattr(state, "synthesized_response", None)
        return {"verification_status": bool(response)}


def _timed_node(node_name: str, fn: NodeFn) -> Callable[[Any], JSONDict]:
    """Wrap a node function to record elapsed time in state['node_timings']."""
    @wraps(fn)
    def wrapper(state: Any) -> JSONDict:
        t0 = time.perf_counter()
        result = _as_json_dict(fn(state))
        elapsed_ms = (time.perf_counter() - t0) * 1000
        elapsed_rounded = round(elapsed_ms, 2)
        node_timings = _node_timings_from_state(state)
        _assign_node_timings(state, node_timings)
        node_timings[node_name] = elapsed_rounded
        logger.info(
            "pipeline node completed",
            extra={
                "node": node_name,
                "duration_ms": elapsed_rounded,
                "budget_ms": PIPELINE_NODE_LATENCY_BUDGET_MS.get(node_name),
            },
        )
        result["node_timings"] = node_timings
        return result
    return wrapper


load_dotenv()

logger = logging.getLogger(__name__)

PIPELINE_NODE_LATENCY_BUDGET_MS: dict[str, int] = {
    "receiver": 25,
    "planner": 250,
    "router": 75,
    "executor": 1200,
    "synthesizer": 1200,
    "verifier": 250,
}


class NRGWorkflow:
    """Main LangGraph workflow for NRG orchestration."""

    def __init__(self, test_mode: bool = False) -> None:
        self.test_mode = test_mode
        self.session_history: dict[str, list[JSONDict]] = {}
        self.checkpointer: Any | None = None
        if os.getenv("ENABLE_LANGGRAPH_CHECKPOINTS", "false").lower() == "true":
            from src.orchestration.checkpoint import get_checkpointer

            self.checkpointer = get_checkpointer()
        self.graph = self._build_graph()

    def _build_graph(self) -> Any:
        workflow = StateGraph(NRGState)

        workflow.add_node("receiver", self._receiver_wrapper)
        workflow.add_node("planner", _timed_node("planner", planner_node))
        workflow.add_node("router", _timed_node("router", router_node))
        workflow.add_node("executor", _timed_node("executor", executor_node))
        workflow.add_node("synthesizer", _timed_node("synthesizer", synthesizer_node))
        workflow.add_node("verifier", _timed_node("verifier", verifier_node))

        workflow.set_entry_point("receiver")
        workflow.add_edge("receiver", "planner")
        workflow.add_edge("planner", "router")
        workflow.add_edge("router", "executor")
        workflow.add_edge("executor", "synthesizer")
        workflow.add_edge("synthesizer", "verifier")

        # Verification loop: retry synthesis if faithfulness < 0.7
        def _should_retry(state: Any) -> str:
            """Conditional edge: retry synthesis if verification indicates low faithfulness."""
            if hasattr(state, "__dataclass_fields__"):
                faithfulness = float(getattr(state, "faithfulness_score", 0.0) or 0.0)
                verification_status = str(getattr(state, "verification_status", "ok") or "ok")
                verification_retries = int(getattr(state, "verification_retries", 0) or 0)
            else:
                state_dict = _as_json_dict(state)
                faithfulness = float(state_dict.get("faithfulness_score", 0.0) or 0.0)
                verification_status = str(state_dict.get("verification_status", "ok") or "ok")
                verification_retries = int(state_dict.get("verification_retries", 0) or 0)

            if verification_retries >= 1:
                return "end_retry"

            if verification_status == "retry" and faithfulness < 0.7:
                return "retry_synthesis"

            return "end_retry"

        # Conditional routing after verifier
        workflow.add_conditional_edges(
            "verifier",
            _should_retry,
            {
                "retry_synthesis": "synthesizer",  # Loop back to re-synthesize with more evidence
                "end_retry": END,
            }
        )

        if self.checkpointer is None:
            return workflow.compile()

        try:
            return workflow.compile(checkpointer=self.checkpointer, store=self.checkpointer)
        except TypeError:
            logger.warning("Checkpoint backend is not LangGraph-native; compiling without it")
            return workflow.compile()

    def _receiver_wrapper(self, state: Any) -> JSONDict:
        t0 = time.perf_counter()
        result = _as_json_dict(receiver_node(state))
        elapsed_ms = (time.perf_counter() - t0) * 1000
        elapsed_rounded = round(elapsed_ms, 2)
        node_timings = _node_timings_from_state(state)
        _assign_node_timings(state, node_timings)
        node_timings["receiver"] = elapsed_rounded
        logger.info(
            "pipeline node completed",
            extra={
                "node": "receiver",
                "duration_ms": elapsed_rounded,
                "budget_ms": PIPELINE_NODE_LATENCY_BUDGET_MS.get("receiver"),
            },
        )
        result["node_timings"] = node_timings
        return result

    def _get_session_history(self, session_id: str) -> list[JSONDict]:
        return list(self.session_history.get(session_id, []))

    def _append_session_turn(self, session_id: str, query: str, result: JSONDict) -> list[JSONDict]:
        history = self.session_history.setdefault(session_id, [])
        history.append(
            {
                "query": query,
                "response": result.get("synthesized_response", ""),
            }
        )
        return list(history)

    @cache_query(ttl=600)
    def run(
        self,
        query: str,
        user_tier: int = 1,
        session_id: str | None = None,
        user_id: str | None = None,
    ) -> JSONDict:
        """Execute a query through the workflow."""
        active_session_id = session_id or str(uuid.uuid4())

        try:
            log_query(user_id or "anonymous", query)
        except Exception:
            logger.warning("Audit log_query failed in workflow", exc_info=True)

        conversation_history = self._get_session_history(active_session_id)
        initial_state = create_initial_state(
            query,
            user_tier,
            session_id=active_session_id,
            conversation_history=conversation_history,
        )

        config: JSONDict = {"configurable": {"thread_id": active_session_id}}
        result = _as_json_dict(self.graph.invoke(initial_state, config))
        result["session_id"] = active_session_id
        result["conversation_history"] = self._append_session_turn(
            active_session_id,
            query,
            result,
        )

        try:
            from src.training.data_collector import capture_training_async

            capture_training_async(result, user_id=user_id)
        except Exception:
            pass

        if self.test_mode:
            self._save_state(result)

        return dict(result)

    def _save_state(self, state: JSONDict) -> None:
        import os

        protocol_dir = Path(os.environ.get("NRG_PROTOCOL_DIR", ".protocol"))
        protocol_dir.mkdir(exist_ok=True)
        state_file = protocol_dir / f"state_{state.get('query_id', 'unknown')}.json"
        state_file.write_text(json.dumps(state, indent=2, default=str))


def main():
    """CLI entry point for manual orchestration checks."""
    import argparse

    parser = argparse.ArgumentParser(description="NRG LangGraph Orchestration")
    parser.add_argument("--test-mode", action="store_true", help="Enable test mode")
    parser.add_argument("--query", type=str, help="Query to execute")
    args = parser.parse_args()

    workflow = NRGWorkflow(test_mode=args.test_mode)

    if args.test_mode:
        from datetime import datetime
        current_year = datetime.now().year
        years_ago = current_year - 3
        test_queries = [
            "Find all robotics researchers in Gujarat",
            "What are the latest advances in sustainable energy at IIT campuses",
            f"Synthesize autonomous robotics research trends and funding data {years_ago}-{current_year}",
        ]
        for query in test_queries:
            print(f"\n{'=' * 60}\nExecuting: {query}\n{'=' * 60}")
            result = workflow.run(query)
            print(f"\nIntent: {result.get('intent')}")
            print(f"Routing: {result.get('routing_decision')}")
            print(f"Response: {result.get('synthesized_response', 'N/A')[:200]}...")
        return

    if args.query:
        result = workflow.run(args.query)
        print(result.get("synthesized_response"))
        return

    print("NRG LangGraph Orchestration Ready")
    print("Use --test-mode or --query <query>")


if __name__ == "__main__":
    main()
