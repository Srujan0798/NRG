"""Router Node - Intent disambiguation and skill routing with confidence scoring.

Phase 1 - Fortify:
  - Graceful degradation with confidence threshold enforcement
  - Edge case handling for empty/single-word/SQL injection/10k+ char queries
  - LLM-based disambiguation with fallback to hybrid

Phase 2 - Elevate:
  - 2-stage routing: fast regex pre-classification + LLM confirmation for ambiguous
  - Intent decomposition for multi-intent queries
  - Route explanation in pipeline state
  - 50-query evaluation dataset

Phase 3 - Immortalize:
  - Self-calibrating confidence tracking
  - Configurable routing rules via environment variables
  - Routing metrics for observability
"""

from __future__ import annotations

from typing import TypedDict, Optional, NamedTuple
import re
import logging
import os
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class IntentType(str, Enum):
    STRUCTURED = "structured"
    UNSTRUCTURED = "unstructured"
    HYBRID = "hybrid"


class RoutingDecision(NamedTuple):
    intent: str
    confidence: float
    routing: str
    rationale: list[str]
    ambiguity_detected: bool = False
    ambiguity_issues: list[str] = []
    clarifications: list[str] = []
    subqueries: list[str] = []
    multi_intent: bool = False
    llm_enhanced: bool = False
    stage: str = "regex"


CONFIDENCE_THRESHOLD_LOW = float(os.getenv("ROUTER_CONFIDENCE_THRESHOLD_LOW", "0.6"))
CONFIDENCE_THRESHOLD_HIGH = float(os.getenv("ROUTER_CONFIDENCE_THRESHOLD_HIGH", "0.8"))
MAX_QUERY_LENGTH = int(os.getenv("ROUTER_MAX_QUERY_LENGTH", "10000"))
ENABLE_2STAGE_ROUTING = os.getenv("ROUTER_ENABLE_2STAGE", "true").lower() == "true"
ENABLE_SELF_CALIBRATION = os.getenv("ROUTER_ENABLE_SELF_CALIBRATION", "true").lower() == "true"


class RouterState(TypedDict):
    """State passed from router node."""

    intent: str
    routing_decision: Optional[str]


INTENT_PATTERNS = {
    "structured": [
        r"(list|find|show|get|count|how many|who has|which\s+\w+)",
        r"(researchers?|labs?|funding|publication|grant|institution)",
        r"(in|at|from|by|with)\s+\w+",
    ],
    "unstructured": [
        r"(what are|explain|describe|summarize|tell me about)",
        r"(trends?|advances?|latest|current|recent|past\s+\d+\s+years?)",
        r"(overview|analysis|insights?|findings?)",
    ],
    "hybrid": [
        r"synthesize",
        r"combine.*with",
        r"integrat",
        r"correlat",
        r"both.*and",
    ],
}

AMBIGUITY_PATTERNS = [
    r"\b(best|top|leading|most|strongest|greatest)\b",
    r"\b(compare|versus|vs|against)\b",
    r"\b(recent|lately|nowadays|currently)\b",
    r"\b(all-time|ever|historically)\b",
    r"\b(who is doing|who works on|who leads|who published)\b",
    r"\b(relationship|correlation|difference)\b",
]

MULTI_INTENT_SEPARATORS = [
    r"\band\b",
    r"\bplus\b",
    r"\bwith\b",
    r";",
    r",\s*(but|and|also)\s+",
    r",\s+(?=[A-Z])",
]

SQL_INJECTION_PATTERNS = [
    r"(\bOR\b|\bAND\b)\s*['\"]?\s*(1|TRUE|FALSE|'')\s*(=|<|>|<=|>=|<>)",
    r"\b(1|TRUE)\s*=\s*1\b",
    r"(DROP|DELETE|INSERT|UPDATE|ALTER|CREATE)\s+(TABLE|DATABASE|INDEX|USER)",
    r"\bDELETE\s+FROM\b",
    r"(--|#|\/\*|\*\/)",
    r"(UNION\s+SELECT|SLEEP\s*\()",
    r"['\"].*['\"].*(OR|AND).*['\"]",
]


class RoutingMetrics:
    """Self-calibrating routing metrics tracker."""

    _instance: Optional["RoutingMetrics"] = None
    _lock = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.total_routes = 0
        self.route_distribution = {"structured": 0, "unstructured": 0, "hybrid": 0}
        self.confidence_sum = 0.0
        self.ambiguity_rate = 0.0
        self.ambiguity_count = 0
        self.llm_enhancement_count = 0
        self.self_calibration_data: list[dict] = []

    @classmethod
    def reset(cls):
        """Reset the singleton state for testing."""
        if cls._instance is not None:
            cls._instance._initialized = False
            cls._instance = None

    def record(
        self,
        intent: str,
        confidence: float,
        is_ambiguous: bool,
        llm_enhanced: bool,
        was_correct: Optional[bool] = None,
    ):
        """Record a routing decision for metrics and self-calibration."""
        self.total_routes += 1
        self.route_distribution[intent] = self.route_distribution.get(intent, 0) + 1
        self.confidence_sum += confidence

        if is_ambiguous:
            self.ambiguity_count += 1
        self.ambiguity_rate = self.ambiguity_count / self.total_routes

        if llm_enhanced:
            self.llm_enhancement_count += 1

        if ENABLE_SELF_CALIBRATION and was_correct is not None:
            self.self_calibration_data.append({
                "timestamp": datetime.now().isoformat(),
                "intent": intent,
                "confidence": confidence,
                "was_correct": was_correct,
            })
            if len(self.self_calibration_data) > 1000:
                self.self_calibration_data = self.self_calibration_data[-500:]

    def get_metrics(self) -> dict:
        """Get current routing metrics."""
        avg_confidence = (
            self.confidence_sum / self.total_routes if self.total_routes > 0 else 0.0
        )
        return {
            "total_routes": self.total_routes,
            "route_distribution": self.route_distribution,
            "avg_confidence": round(avg_confidence, 3),
            "ambiguity_rate": round(self.ambiguity_rate, 3),
            "llm_enhancement_rate": round(
                self.llm_enhancement_count / self.total_routes, 3
            )
            if self.total_routes > 0
            else 0.0,
            "self_calibration_samples": len(self.self_calibration_data),
        }

    def recalibrate_confidence(
        self, intent: str, observed_accuracy: float
    ) -> dict[str, float]:
        """Recalibrate confidence thresholds based on observed accuracy."""
        if len(self.self_calibration_data) < 10:
            return {}

        recent_data = [
            d for d in self.self_calibration_data[-100:] if d["intent"] == intent
        ]
        if len(recent_data) < 5:
            return {}

        correct = sum(1 for d in recent_data if d["was_correct"])
        accuracy = correct / len(recent_data)

        calibration_factor = accuracy / 0.85
        adjustment = max(0.8, min(1.2, calibration_factor))

        return {
            "intent": intent,
            "observed_accuracy": round(accuracy, 3),
            "calibration_factor": round(adjustment, 3),
            "samples": len(recent_data),
        }


def _is_sql_injection_attempt(query: str) -> bool:
    """Detect potential SQL injection attempts."""
    query_lower = query.lower()
    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, query_lower, re.IGNORECASE):
            logger.warning("SQL injection pattern detected in query: %s", query[:100])
            return True
    return False


def _sanitize_query(query: str) -> str:
    """Sanitize query by truncating and normalizing whitespace."""
    query = query.strip()
    if len(query) > MAX_QUERY_LENGTH:
        logger.info("Query truncated from %d to %d chars", len(query), MAX_QUERY_LENGTH)
        query = query[:MAX_QUERY_LENGTH]
    query = re.sub(r"\s+", " ", query)
    return query


def _detect_ambiguity(query: str) -> tuple[bool, list[str]]:
    """Detect ambiguous terms and return (is_ambiguous, list_of_issues)."""
    issues = []
    query_lower = query.lower()
    for pattern in AMBIGUITY_PATTERNS:
        match = re.search(pattern, query_lower)
        if match:
            issues.append(match.group(0))
    return len(issues) > 0, issues


def _detect_multi_intent(query: str) -> tuple[bool, list[str]]:
    """Detect if query contains multiple intents that need decomposition."""
    subqueries = []
    query_lower = query.lower()

    for separator in MULTI_INTENT_SEPARATORS:
        parts = re.split(separator, query_lower, maxsplit=2, flags=re.IGNORECASE)
        if len(parts) > 1:
            for part in parts:
                part = part.strip()
                if len(part) > 10:
                    subqueries.append(part)

    if len(subqueries) < 2:
        sentences = re.split(r"[?;]", query_lower)
        valid_subqueries = [s.strip() for s in sentences if len(s.strip()) > 20]
        if len(valid_subqueries) > 1:
            subqueries = valid_subqueries

    return len(subqueries) >= 2, subqueries


def _classify_intent_with_confidence(query: str) -> tuple[str, float, dict]:
    """Classify query intent based on patterns with confidence scoring.

    Returns:
        tuple: (intent, confidence_score, scoring_details)
    """
    query_lower = query.lower()

    scores = {"structured": 0, "unstructured": 0, "hybrid": 0}
    matched_patterns: dict[str, list[str]] = {
        "structured": [],
        "unstructured": [],
        "hybrid": [],
    }

    for intent, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, query_lower, re.IGNORECASE):
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

    return "unstructured", 0.5, {
        "scores": scores,
        "matched_patterns": [],
        "reason": "fallback",
    }


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


MULTI_INTENT_DECOMPOSITION_PROMPT = """You are a query decomposer for a national research graph query system.

Decompose this complex query into 2-3 simpler sub-queries that can each be answered independently.

Each sub-query should:
1. Be self-contained (no dependencies on other sub-query results)
2. Target a single intent (structured data OR document analysis, not both)
3. Be answerable with the available tools (text-to-sql for data, RAG for documents)

Original Query: {query}

Return a JSON array of sub-queries:
["sub-query 1", "sub-query 2", ...]

If the query is already simple, return it as a single-element array."""


def _classify_intent_via_llm(query: str) -> Optional[str]:
    """Classify intent using Minimax LLM (primary) or local LLM (fallback)."""
    try:
        from src.config.llm_config import get_llm_client

        client = get_llm_client("minimax")
        if client is None:
            try:
                from src.config.local_llm import get_local_llm_client

                client = get_local_llm_client()
            except ImportError:
                return None
        if client is None:
            return None

        prompt = INTENT_CLASSIFICATION_PROMPT.format(query=query)
        response = client.generate(
            system_prompt="You are a query intent classifier. Return ONLY the intent word: structured, unstructured, or hybrid.",
            user_prompt=prompt,
            conversation_history=[],
        )
        response_lower = response.strip().lower()

        for intent in ("structured", "unstructured", "hybrid"):
            if intent in response_lower:
                logger.info(
                    "LLM intent classification (Minimax): %s -> %s", query[:50], intent
                )
                return intent
        return None
    except Exception as e:
        logger.warning("LLM intent classification failed: %s", e)
        return None


def _decompose_intent_via_llm(query: str) -> list[str]:
    """Decompose multi-intent query into sub-queries using LLM."""
    try:
        from src.config.llm_config import get_llm_client

        client = get_llm_client("minimax")
        if client is None:
            try:
                from src.config.local_llm import get_local_llm_client

                client = get_local_llm_client()
            except ImportError:
                return [query]
        if client is None:
            return [query]

        prompt = MULTI_INTENT_DECOMPOSITION_PROMPT.format(query=query)
        response = client.generate(
            system_prompt="You are a query decomposer. Return ONLY a JSON array of strings.",
            user_prompt=prompt,
            conversation_history=[],
        )

        import json

        try:
            subqueries = json.loads(response)
            if isinstance(subqueries, list) and all(isinstance(q, str) for q in subqueries):
                logger.info(
                    "LLM decomposed query into %d sub-queries", len(subqueries)
                )
                return subqueries
        except json.JSONDecodeError:
            match = re.search(r"\[.*\]", response, re.DOTALL)
            if match:
                subqueries = json.loads(match.group(0))
                if isinstance(subqueries, list):
                    return subqueries

        return [query]
    except Exception as e:
        logger.warning("LLM intent decomposition failed: %s", e)
        return [query]


def _apply_default_clarifications(query: str) -> list[str]:
    """Apply default clarifications for ambiguous terms."""
    clarifications = []
    query_lower = query.lower()

    if "best" in query_lower or "top" in query_lower:
        clarifications.append("Assumption: 'best' = most publications in last 5 years")
    if "compare" in query_lower or "versus" in query_lower or " vs " in query_lower:
        clarifications.append("Assumption: compare = publication count and funding")
    if "recent" in query_lower or "currently" in query_lower or "lately" in query_lower:
        current_year = datetime.now().year
        years_ago = current_year - 3
        clarifications.append(
            f"Assumption: 'recent' = last 3 years ({years_ago}-{current_year})"
        )
    if "leading" in query_lower or "strongest" in query_lower:
        clarifications.append("Assumption: 'leading' = highest h-index score")

    return clarifications


def _stage1_regex_classification(
    user_query: str,
) -> tuple[str, float, dict, bool, list[str]]:
    """Stage 1: Fast regex-based classification.

    Returns:
        tuple: (intent, confidence, details, is_ambiguous, ambiguity_issues)
    """
    intent, confidence, details = _classify_intent_with_confidence(user_query)
    is_ambiguous, ambiguity_issues = _detect_ambiguity(user_query)

    details["stage"] = "regex"
    return intent, confidence, details, is_ambiguous, ambiguity_issues


def _stage2_llm_confirmation(
    user_query: str,
    intent: str,
    confidence: float,
    is_ambiguous: bool,
    ambiguity_issues: list[str],
) -> tuple[str, float, bool, list[str], list[str], bool]:
    """Stage 2: LLM confirmation for low-confidence or ambiguous queries.

    Returns:
        tuple: (resolved_intent, resolved_confidence, is_ambiguous, issues, clarifications, llm_enhanced)
    """
    if not is_ambiguous and confidence >= CONFIDENCE_THRESHOLD_HIGH:
        return intent, confidence, is_ambiguous, ambiguity_issues, [], False

    clarifications = []
    llm_enhanced = False

    if is_ambiguous or confidence < CONFIDENCE_THRESHOLD_HIGH:
        llm_intent = _classify_intent_via_llm(user_query)
        if llm_intent:
            resolved_intent = llm_intent
            resolved_confidence = 0.85
            llm_enhanced = True
            logger.info(
                "LLM enhanced routing: %s (conf %.2f) -> %s (conf %.2f)",
                intent,
                confidence,
                llm_intent,
                resolved_confidence,
            )
            return (
                resolved_intent,
                resolved_confidence,
                False,
                ambiguity_issues,
                clarifications,
                llm_enhanced,
            )

    if is_ambiguous:
        clarifications = _apply_default_clarifications(user_query)
        if intent != "hybrid":
            return "hybrid", 0.75, True, ambiguity_issues, clarifications, llm_enhanced

    return intent, confidence, is_ambiguous, ambiguity_issues, clarifications, llm_enhanced


def router_node(state) -> dict:
    """Route query to appropriate skill(s) with confidence scoring and rationale.

    2-stage routing:
      Stage 1: Fast regex pre-classification (always runs)
      Stage 2: LLM confirmation for ambiguous (confidence < 0.8) queries

    Args:
        state: Pipeline state with user_query

    Returns:
        dict: Routing decision with intent, confidence, rationale, and metadata
    """
    metrics = RoutingMetrics()

    plan = state.get("plan") if isinstance(state, dict) else getattr(state, "plan", None)

    if isinstance(plan, dict) and plan.get("desired_skills"):
        desired = {str(skill).lower() for skill in plan["desired_skills"]}
        if "sql+rag" in desired or {"sql", "rag"}.issubset(desired):
            result = {
                "intent": "hybrid",
                "routing_decision": "text_to_sql+rag",
                "routing_confidence": 0.95,
                "routing_rationale": [
                    "Source: planner",
                    f"Desired skills from plan: {desired}",
                    "Both SQL and RAG requested",
                ],
                "plan_skills_used": True,
                "multi_intent": False,
                "subqueries": [],
                "is_ambiguous": False,
                "ambiguity_issues": [],
                "clarifications": [],
                "llm_enhanced": False,
                "stage": "planner",
            }
            metrics.record("hybrid", 0.95, False, False)
            return result

        if "sql" in desired:
            result = {
                "intent": "structured",
                "routing_decision": "text_to_sql",
                "routing_confidence": 0.9,
                "routing_rationale": [
                    "Source: planner",
                    f"Desired skills from plan: {desired}",
                    "SQL-only requested",
                ],
                "plan_skills_used": True,
                "multi_intent": False,
                "subqueries": [],
                "is_ambiguous": False,
                "ambiguity_issues": [],
                "clarifications": [],
                "llm_enhanced": False,
                "stage": "planner",
            }
            metrics.record("structured", 0.9, False, False)
            return result

        if "rag" in desired:
            result = {
                "intent": "unstructured",
                "routing_decision": "rag",
                "routing_confidence": 0.9,
                "routing_rationale": [
                    "Source: planner",
                    f"Desired skills from plan: {desired}",
                    "RAG-only requested",
                ],
                "plan_skills_used": True,
                "multi_intent": False,
                "subqueries": [],
                "is_ambiguous": False,
                "ambiguity_issues": [],
                "clarifications": [],
                "llm_enhanced": False,
                "stage": "planner",
            }
            metrics.record("unstructured", 0.9, False, False)
            return result

    if hasattr(state, "user_query"):
        user_query = state.user_query
    elif isinstance(state, dict):
        user_query = state.get("user_query", "")
    else:
        user_query = ""

    if not user_query or not user_query.strip():
        logger.warning("Empty query received, defaulting to hybrid")
        result = {
            "intent": "hybrid",
            "routing_decision": "text_to_sql+rag",
            "routing_confidence": 0.3,
            "routing_rationale": ["Edge case: empty query, defaulting to hybrid"],
            "plan_skills_used": False,
            "multi_intent": False,
            "subqueries": [],
            "is_ambiguous": True,
            "ambiguity_issues": ["empty_query"],
            "clarifications": ["Default: search both structured data and documents"],
            "llm_enhanced": False,
            "stage": "edge_case",
        }
        metrics.record("hybrid", 0.3, True, False)
        return result

    if _is_sql_injection_attempt(user_query):
        logger.warning("SQL injection attempt detected, routing to safe hybrid mode")
        result = {
            "intent": "hybrid",
            "routing_decision": "text_to_sql+rag",
            "routing_confidence": 0.2,
            "routing_rationale": [
                "Security: SQL injection pattern detected",
                "Routing to safe hybrid mode for manual review",
            ],
            "plan_skills_used": False,
            "multi_intent": False,
            "subqueries": [],
            "is_ambiguous": True,
            "ambiguity_issues": ["sql_injection_detected"],
            "clarifications": ["Manual review recommended for security"],
            "llm_enhanced": False,
            "stage": "security",
        }
        metrics.record("hybrid", 0.2, True, False)
        return result

    user_query = _sanitize_query(user_query)

    if len(user_query.split()) == 1:
        logger.info("Single-word query detected: %s", user_query)
        result = {
            "intent": "unstructured",
            "routing_decision": "rag",
            "routing_confidence": 0.4,
            "routing_rationale": [
                "Edge case: single-word query",
                "Defaulting to document search (RAG)",
            ],
            "plan_skills_used": False,
            "multi_intent": False,
            "subqueries": [user_query],
            "is_ambiguous": True,
            "ambiguity_issues": ["single_word_query"],
            "clarifications": ["Single word interpreted as topic search"],
            "llm_enhanced": False,
            "stage": "edge_case",
        }
        metrics.record("unstructured", 0.4, True, False)
        return result

    is_multi_intent, subqueries = _detect_multi_intent(user_query)

    intent, confidence, details, is_ambiguous, ambiguity_issues = _stage1_regex_classification(
        user_query
    )

    if ENABLE_2STAGE_ROUTING and (is_ambiguous or confidence < CONFIDENCE_THRESHOLD_HIGH):
        intent, confidence, is_ambiguous, ambiguity_issues, clarifications, llm_enhanced = _stage2_llm_confirmation(
            user_query, intent, confidence, is_ambiguous, ambiguity_issues
        )
        details["stage"] = "llm"
    else:
        clarifications = []
        llm_enhanced = False
        if is_ambiguous:
            clarifications = _apply_default_clarifications(user_query)
            if intent != "hybrid" and confidence < CONFIDENCE_THRESHOLD_LOW:
                intent = "hybrid"
                confidence = CONFIDENCE_THRESHOLD_LOW

    if confidence < CONFIDENCE_THRESHOLD_LOW:
        if intent != "hybrid":
            logger.info(
                "Confidence %.2f below threshold %.2f, upgrading to hybrid",
                confidence,
                CONFIDENCE_THRESHOLD_LOW,
            )
            intent = "hybrid"
            confidence = CONFIDENCE_THRESHOLD_LOW
            if not clarifications:
                clarifications = ["Low confidence, using hybrid for safety"]

    routing_decision = _route_to_skill(intent)

    rationale = [
        f"Stage: {details.get('stage', 'unknown')}",
        f"Intent: {intent}",
        f"Confidence: {confidence:.2f}",
        f"Threshold check: {'PASS' if confidence >= CONFIDENCE_THRESHOLD_LOW else 'FAIL (forced hybrid)'}",
        f"Matched patterns: {details.get('matched_patterns', [])}",
        f"Reason: {details.get('reason', 'N/A')}",
    ]
    if is_ambiguous:
        rationale.append(f"Ambiguity: {ambiguity_issues}")
    if llm_enhanced:
        rationale.append("LLM enhanced classification")
    if is_multi_intent:
        rationale.append(f"Multi-intent decomposed: {len(subqueries)} sub-queries")

    logger.info(
        "Routing: query=%s intent=%s conf=%.2f route=%s multi=%s llm=%s",
        user_query[:50],
        intent,
        confidence,
        routing_decision,
        is_multi_intent,
        llm_enhanced,
    )

    metrics.record(intent, confidence, is_ambiguous, llm_enhanced)

    return {
        "intent": intent,
        "routing_decision": routing_decision,
        "routing_confidence": confidence,
        "routing_rationale": rationale,
        "plan_skills_used": False,
        "multi_intent": is_multi_intent,
        "subqueries": subqueries if is_multi_intent else [],
        "is_ambiguous": is_ambiguous,
        "ambiguity_issues": ambiguity_issues,
        "clarifications": clarifications,
        "llm_enhanced": llm_enhanced,
        "stage": details.get("stage", "regex"),
    }
