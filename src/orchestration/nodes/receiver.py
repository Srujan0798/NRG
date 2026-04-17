"""Receiver Node - Entry point for user queries."""

from typing import TypedDict
import uuid
from datetime import datetime


class ReceiverState(TypedDict):
    """State passed from receiver node."""

    query_id: str
    session_id: str
    user_query: str
    user_tier: int
    conversation_history: list
    created_at: str


def receiver_node(state):
    """Process incoming user query and initialize state."""
    if hasattr(state, "query_id"):
        query_id = state.query_id or str(uuid.uuid4())
    elif isinstance(state, dict):
        query_id = state.get("query_id", str(uuid.uuid4()))
    else:
        query_id = str(uuid.uuid4())

    if hasattr(state, "session_id"):
        session_id = state.session_id or query_id
    elif isinstance(state, dict):
        session_id = state.get("session_id", query_id)
    else:
        session_id = query_id

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

    if hasattr(state, "conversation_history"):
        conversation_history = state.conversation_history
    elif isinstance(state, dict):
        conversation_history = state.get("conversation_history", [])
    else:
        conversation_history = []

    return {
        "query_id": query_id,
        "session_id": session_id,
        "user_query": user_query,
        "user_tier": user_tier,
        "conversation_history": conversation_history,
        "created_at": datetime.utcnow().isoformat(),
    }


def create_initial_state(
    user_query: str,
    user_tier: int = 1,
    session_id: str | None = None,
    conversation_history: list | None = None,
) -> dict:
    """Create initial state for a new query."""
    query_id = str(uuid.uuid4())
    return {
        "query_id": query_id,
        "session_id": session_id or query_id,
        "user_query": user_query,
        "user_tier": user_tier,
        "conversation_history": conversation_history or [],
    }
