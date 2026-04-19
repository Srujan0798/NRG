"""LangGraph orchestration for the Phase 1 NRG query workflow."""

from __future__ import annotations

import json
import logging
import os
import uuid
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langgraph.graph import END, StateGraph

from src.audit import log_query
from src.caching.redis_layer import cache_query
from src.orchestration.nodes.executor import executor_node
from src.orchestration.nodes.receiver import create_initial_state, receiver_node
from src.orchestration.nodes.router import router_node
from src.orchestration.nodes.synthesizer import synthesizer_node
from src.orchestration.state import NRGState

try:
    from src.orchestration.nodes.planner import planner_node
except ModuleNotFoundError:

    def planner_node(state: Any) -> dict:
        """Phase 1 fallback planner.

        The experimental cloud planner is quarantined until it is wired through
        the evidence/egress policy. Router heuristics remain the active path.
        """
        return {"plan": None}


try:
    from src.orchestration.nodes.verifier import verifier_node
except ModuleNotFoundError:

    def verifier_node(state: Any) -> dict:
        """Phase 1 fallback verifier."""
        if isinstance(state, dict):
            response = state.get("synthesized_response")
        else:
            response = getattr(state, "synthesized_response", None)
        return {"verification_status": bool(response)}


load_dotenv()

logger = logging.getLogger(__name__)


class NRGWorkflow:
    """Main LangGraph workflow for NRG orchestration."""

    def __init__(self, test_mode: bool = False):
        self.test_mode = test_mode
        self.session_history: dict[str, list[dict]] = {}
        self.checkpointer = None
        if os.getenv("ENABLE_LANGGRAPH_CHECKPOINTS", "false").lower() == "true":
            from src.orchestration.checkpoint import get_checkpointer

            self.checkpointer = get_checkpointer()
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(NRGState)

        workflow.add_node("receiver", self._receiver_wrapper)
        workflow.add_node("planner", planner_node)
        workflow.add_node("router", router_node)
        workflow.add_node("executor", executor_node)
        workflow.add_node("synthesizer", synthesizer_node)
        workflow.add_node("verifier", verifier_node)

        workflow.set_entry_point("receiver")
        workflow.add_edge("receiver", "planner")
        workflow.add_edge("planner", "router")
        workflow.add_edge("router", "executor")
        workflow.add_edge("executor", "synthesizer")
        workflow.add_edge("synthesizer", "verifier")
        workflow.add_edge("verifier", END)

        if self.checkpointer is None:
            return workflow.compile()

        try:
            return workflow.compile(checkpointer=self.checkpointer, store=self.checkpointer)
        except TypeError:
            logger.warning("Checkpoint backend is not LangGraph-native; compiling without it")
            return workflow.compile()

    def _receiver_wrapper(self, state: dict) -> dict:
        return receiver_node(state)

    def _get_session_history(self, session_id: str) -> list[dict]:
        return list(self.session_history.get(session_id, []))

    def _append_session_turn(self, session_id: str, query: str, result: dict) -> list[dict]:
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
    ) -> dict:
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

        config = {"configurable": {"thread_id": active_session_id}}
        result = self.graph.invoke(initial_state, config)
        result["session_id"] = active_session_id
        result["conversation_history"] = self._append_session_turn(
            active_session_id,
            query,
            result,
        )

        if self.test_mode:
            self._save_state(result)

        return result

    def _save_state(self, state: dict) -> None:
        protocol_dir = Path(".protocol")
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
        test_queries = [
            "Find all robotics researchers in Gujarat",
            "What are the latest advances in sustainable energy at IIT campuses",
            "Synthesize autonomous robotics research trends and funding data 2021-2024",
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
