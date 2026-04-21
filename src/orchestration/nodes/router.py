"""Router Node - Intent disambiguation and skill routing with confidence scoring."""

from typing import TypedDict, Optional
import re
import logging
import os

logger = logging.getLogger(__name__)


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


def _classify_intent_with_confidence(query: str) -> tuple[str, float, dict]:
    """Classify query intent based on patterns with confidence scoring.

    Returns:
        tuple: (intent, confidence_score, scoring_details)
    """
    query_lower = query.lower()

    scores = {"structured": 0, "unstructured": 0, "hybrid": 0}
    matched_patterns: dict[str, list[str]] = {"structured": [], "unstructured": [], "hybrid": []}

    for intent, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, query_lower):
                scores[intent] += 1
                matched_patterns[intent].append(pattern)

    total_matches = sum(scores.values())
    max_score = max(scores.values())

    if scores["hybrid"] > 0 and (scores["structured"] > 0 or scores["unstructured"] > 0):
        confidence = min(0.95, 0.5 + (scores["hybrid"] * 0.15))
        return "hybrid", confidence, {
            "scores": scores,
            "matched_patterns": matched_patterns["hybrid"],
            "reason": "hybrid keywords combined with structured/unstructured",
        }

    if max_score == 0:
        return "unstructured", 0.5, {
            "scores": scores,
            "matched_patterns": [],
            "reason": "no patterns matched, defaulting to unstructured",
        }

    confidence = min(0.9, 0.4 + (max_score * 0.2) + (total_matches * 0.05))

    for intent, score in scores.items():
        if score == max_score:
            return intent, confidence, {
                "scores": scores,
                "matched_patterns": matched_patterns[intent],
                "reason": f"highest score ({score}) for {intent}",
            }

    return "unstructured", 0.5, {"scores": scores, "matched_patterns": [], "reason": "fallback"}


def _route_to_skill(intent: str) -> str:
    """Map intent to skill execution."""
    routing_map = {
        "structured": "text_to_sql",
        "unstructured": "rag",
        "hybrid": "text_to_sql+rag",
    }
    return routing_map.get(intent, "rag")


INTENT_CLASSIFICATION_PROMPT = """You are an intent classifier for a national research graph query system.

Classify this query as ONE of three intents:
- structured: The query asks for specific data (counts, lists, facts about researchers, publications, labs, funding, institutions). Examples: "list researchers in Gujarat", "count publications in 2023", "show funding for AI projects"
- unstructured: The query asks for understanding, explanations, trends, or analysis from documents. Examples: "what are trends in AI research", "explain hydrogen catalysis breakthroughs", "summarize research directions in quantum computing"
- hybrid: The query clearly needs BOTH structured data AND document analysis. Examples: "find researchers in ML and explain their recent work", "list top funded projects and analyze their impact"

Query: {query}

Respond with ONLY one word: structured, unstructured, or hybrid"""


def _classify_intent_via_llm(query: str) -> Optional[str]:
    """Classify intent using local LLM. Returns None if LLM unavailable."""
    try:
        from src.config.local_llm import get_local_llm_client
        client = get_local_llm_client()
        if client is None:
            return None

        prompt = INTENT_CLASSIFICATION_PROMPT.format(query=query)
        response = client.generate(
            system_prompt="You are a query intent classifier.",
            user_prompt=prompt,
            conversation_history=None,
        )
        response_lower = response.strip().lower()

        for intent in ("structured", "unstructured", "hybrid"):
            if intent in response_lower:
                logger.info("LLM intent classification: %s -> %s", query[:50], intent)
                return intent
        return None
    except Exception as e:
        logger.warning("LLM intent classification failed: %s", e)
        return None


def router_node(state):
    """Route query to appropriate skill(s) with confidence scoring and rationale."""
    plan = state.get("plan") if isinstance(state, dict) else getattr(state, "plan", None)

    if isinstance(plan, dict) and plan.get("desired_skills"):
        desired = {str(skill).lower() for skill in plan["desired_skills"]}
        if "sql+rag" in desired or {"sql", "rag"}.issubset(desired):
            return {
                "intent": "hybrid",
                "routing_decision": "text_to_sql+rag",
                "routing_confidence": 0.95,
                "routing_rationale": [
                    "Source: planner",
                    f"Desired skills from plan: {desired}",
                    "Both SQL and RAG requested",
                ],
                "plan_skills_used": True,
            }
        if "sql" in desired:
            return {
                "intent": "structured",
                "routing_decision": "text_to_sql",
                "routing_confidence": 0.9,
                "routing_rationale": [
                    "Source: planner",
                    f"Desired skills from plan: {desired}",
                    "SQL-only requested",
                ],
                "plan_skills_used": True,
            }
        if "rag" in desired:
            return {
                "intent": "unstructured",
                "routing_decision": "rag",
                "routing_confidence": 0.9,
                "routing_rationale": [
                    "Source: planner",
                    f"Desired skills from plan: {desired}",
                    "RAG-only requested",
                ],
                "plan_skills_used": True,
            }

    if hasattr(state, "user_query"):
        user_query = state.user_query
    elif isinstance(state, dict):
        user_query = state.get("user_query", "")
    else:
        user_query = ""

    intent, confidence, scoring_details = _classify_intent_with_confidence(user_query)
    routing_decision = _route_to_skill(intent)

    rationale = [
        "Source: heuristic_pattern_matching",
        f"Intent classified as: {intent}",
        f"Confidence score: {confidence:.2f}",
        f"Matched patterns: {scoring_details.get('matched_patterns', [])}",
        f"Reason: {scoring_details.get('reason', 'N/A')}",
    ]

    is_ambiguous, ambiguity_issues = _detect_ambiguity(user_query)
    clarifications = []

    if is_ambiguous:
        llm_intent = _classify_intent_via_llm(user_query)
        if llm_intent:
            resolved_intent = llm_intent
            resolved_routing = _route_to_skill(llm_intent)
            confidence = 0.85
            rationale = [
                "Source: llm_disambiguation",
                f"Intent classified as: {llm_intent} (via local LLM)",
                f"Confidence score: {confidence:.2f}",
                f"Ambiguity resolved: {ambiguity_issues}",
            ]
            intent = resolved_intent
            routing_decision = resolved_routing
        else:
            if "best" in user_query.lower() or "top" in user_query.lower():
                clarifications.append("Assumption: 'best' = most publications in last 5 years")
            if "compare" in user_query.lower() or "versus" in user_query.lower():
                clarifications.append("Assumption: compare = publication count and funding")
            if "recent" in user_query.lower() or "currently" in user_query.lower():
                from datetime import datetime
                current_year = datetime.now().year
                years_ago = current_year - 3
                clarifications.append(f"Assumption: 'recent' = last 3 years ({years_ago}-{current_year})")
            if not clarifications:
                clarifications.append("Assumption: query interpreted as general research overview")

            confidence = min(confidence + 0.1, 0.95)
            rationale.append(f"Ambiguity detected: {ambiguity_issues}")
            rationale.append("Auto-upgraded to hybrid for richer context (LLM unavailable)")

            if intent != "hybrid":
                intent = "hybrid"
                routing_decision = "text_to_sql+rag"

    logger.info(
        "Routing decision: intent=%s confidence=%.2f routing=%s rationale=%s",
        intent,
        confidence,
        routing_decision,
        scoring_details.get("reason", "N/A"),
    )

    return {
        "intent": intent,
        "routing_decision": routing_decision,
        "routing_confidence": confidence,
        "routing_rationale": rationale,
        "is_ambiguous": is_ambiguous,
        "ambiguity_issues": ambiguity_issues,
        "clarifications": clarifications,
        "plan_skills_used": False,
    }
