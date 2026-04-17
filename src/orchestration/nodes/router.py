"""Router Node - Intent disambiguation and skill routing."""

from typing import TypedDict, Optional
import re


class RouterState(TypedDict):
    """State passed from router node."""

    intent: str
    routing_decision: Optional[str]


INTENT_PATTERNS = {
    "structured": [
        r"(list|find|show|get|count|how many)",
        r"(researchers?|labs?|funding|publication)",
        r"(in|at|from)\s+\w+",
    ],
    "unstructured": [
        r"(what are|explain|describe|summarize)",
        r"(trends?|advances?|latest|current)",
        r"(overview|analysis)",
    ],
    "hybrid": [
        r"synthesize",
        r"combine",
        r"integrat",
    ],
}


def _classify_intent(query: str) -> str:
    """Classify query intent based on patterns."""
    query_lower = query.lower()

    scores = {"structured": 0, "unstructured": 0, "hybrid": 0}

    for intent, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, query_lower):
                scores[intent] += 1

    if scores["hybrid"] > 0 and (
        scores["structured"] > 0 or scores["unstructured"] > 0
    ):
        return "hybrid"

    max_score = max(scores.values())
    if max_score == 0:
        return "unstructured"

    for intent, score in scores.items():
        if score == max_score:
            return intent

    return "unstructured"


def _route_to_skill(intent: str) -> str:
    """Map intent to skill execution."""
    routing_map = {
        "structured": "text_to_sql",
        "unstructured": "rag",
        "hybrid": "text_to_sql+rag",
    }
    return routing_map.get(intent, "rag")


def router_node(state):
    """Route query to appropriate skill(s)."""
    # Extract user query from state object
    if hasattr(state, "user_query"):
        user_query = state.user_query
    elif isinstance(state, dict):
        user_query = state.get("user_query", "")
    else:
        user_query = ""

    intent = _classify_intent(user_query)
    routing_decision = _route_to_skill(intent)

    return {
        "intent": intent,
        "routing_decision": routing_decision,
    }
