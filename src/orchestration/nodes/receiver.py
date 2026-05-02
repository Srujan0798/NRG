"""Receiver Node - Entry point for user queries."""

from typing import Any, TypedDict, cast
import uuid
from datetime import datetime, UTC


class ReceiverState(TypedDict):
    """State passed from receiver node."""

    query_id: str
    session_id: str
    user_query: str
    user_tier: int
    conversation_history: list[dict[str, Any]]
    created_at: str


def _state_get(state: Any, key: str, default: Any) -> Any:
    if isinstance(state, dict):
        return cast(dict[str, Any], state).get(key, default)
    return getattr(state, key, default)


def receiver_node(state: Any) -> dict[str, Any]:
    """Process incoming user query and initialize state."""
    query_id = _state_get(state, "query_id", "") or str(uuid.uuid4())
    session_id = _state_get(state, "session_id", query_id) or query_id
    user_query = _state_get(state, "user_query", "") or ""
    user_tier = _state_get(state, "user_tier", 1) or 1
    raw_history = _state_get(state, "conversation_history", [])
    conversation_history = cast(list[dict[str, Any]], raw_history) if isinstance(raw_history, list) else []

    return {
        "query_id": query_id,
        "session_id": session_id,
        "user_query": user_query,
        "user_tier": user_tier,
        "conversation_history": conversation_history,
        "created_at": datetime.now(UTC).isoformat(),
    }


def create_initial_state(
    user_query: str,
    user_tier: int = 1,
    session_id: str | None = None,
    conversation_history: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Create initial state for a new query."""
    query_id = str(uuid.uuid4())
    return {
        "query_id": query_id,
        "session_id": session_id or query_id,
        "user_query": user_query,
        "user_tier": user_tier,
        "conversation_history": conversation_history or [],
    }
