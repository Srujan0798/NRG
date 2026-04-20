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

# Ambiguous terms that require assumption-making or clarification
AMBIGUITY_PATTERNS = [
    r"\b(best|top|leading|most|strongest|greatest)\b",
    r"\b(compare|versus|vs|against)\b",
    r"\b(recent|lately|nowadays|currently)\b",
    r"\b(all-time|ever|historically)\b",
    r"\b(who is doing|who works on|who leads)\b",
]


def _detect_ambiguity(query: str) -> tuple[bool, list[str]]:
    """Detect ambiguous terms and return (is_ambiguous, list_of_issues)."""
    issues = []
    query_lower = query.lower()
    for pattern in AMBIGUITY_PATTERNS:
        match = re.search(pattern, query_lower)
        if match:
            issues.append(match.group(0))
    return len(issues) > 0, issues


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
    plan = state.get("plan") if isinstance(state, dict) else getattr(state, "plan", None)
    if isinstance(plan, dict) and plan.get("desired_skills"):
        desired = {str(skill).lower() for skill in plan["desired_skills"]}
        if "sql+rag" in desired or {"sql", "rag"}.issubset(desired):
            return {"intent": "hybrid", "routing_decision": "text_to_sql+rag"}
        if "sql" in desired:
            return {"intent": "structured", "routing_decision": "text_to_sql"}
        if "rag" in desired:
            return {"intent": "unstructured", "routing_decision": "rag"}

    # Extract user query from state object
    if hasattr(state, "user_query"):
        user_query = state.user_query
    elif isinstance(state, dict):
        user_query = state.get("user_query", "")
    else:
        user_query = ""

    intent = _classify_intent(user_query)
    routing_decision = _route_to_skill(intent)

    # Ambiguity detection (Core AI Challenge)
    is_ambiguous, ambiguity_issues = _detect_ambiguity(user_query)
    clarifications = []
    if is_ambiguous:
        # For PoC: auto-resolve with reasonable assumptions rather than asking user
        if "best" in user_query.lower() or "top" in user_query.lower():
            clarifications.append("Assumption: 'best' = most publications in last 5 years")
        if "compare" in user_query.lower() or "versus" in user_query.lower():
            clarifications.append("Assumption: compare = publication count and funding")
        if "recent" in user_query.lower() or "currently" in user_query.lower():
            clarifications.append("Assumption: 'recent' = last 3 years (2022-2025)")
        if not clarifications:
            clarifications.append("Assumption: query interpreted as general research overview")
        # Ambiguous queries benefit from both structured data AND document context
        if intent != "hybrid":
            intent = "hybrid"
            routing_decision = "text_to_sql+rag"

    return {
        "intent": intent,
        "routing_decision": routing_decision,
        "is_ambiguous": is_ambiguous,
        "ambiguity_issues": ambiguity_issues,
        "clarifications": clarifications,
    }
