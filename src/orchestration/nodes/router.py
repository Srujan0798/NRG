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

from collections.abc import Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Any, NamedTuple, Optional, Protocol, TypedDict, cast
import json
import re
import logging
import os
import hashlib
import time as time_module
from datetime import datetime
from enum import Enum

from src.orchestration.query_catalog import QueryClassification, classify_query


logger = logging.getLogger(__name__)

JSONDict = dict[str, Any]


class RouterLLM(Protocol):
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        conversation_history: list[JSONDict],
    ) -> str: ...


def _as_json_dict(value: Any) -> JSONDict:
    if not isinstance(value, Mapping):
        return {}
    return dict(cast(Mapping[str, Any], value))


def _as_string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in cast(list[Any], value)]
    return []


def _state_get(state: Any, key: str, default: Any) -> Any:
    if isinstance(state, Mapping):
        return cast(Mapping[str, Any], state).get(key, default)
    return getattr(state, key, default)


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

COMPLEXITY_ORDER = ("trivial", "simple", "moderate", "complex", "synthesis_heavy")
TIER_COMPLEXITY_LIMITS = {
    1: "moderate",
    2: "complex",
    3: "synthesis_heavy",
}


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
        r"(papers?|publications?\s+about|research\s+on)",
        r"(breakthroughs?|methodology|approaches?|novel)",
        r"(synthesis|synthesize|findings|results?)",
        r"(newest|latest|recent).*(?:research|area|field|topic)",
        r"(vulnerabilities?|cybersecurity|security)",
    ],
    "hybrid": [
        r"synthesize",
        r"combine.*with",
        r"integrat",
        r"correlat",
        r"both.*and",
        r"versus",
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
    r"\bversus\b",
    r"\bvs\b",
    r"\bbut\b",
    r"\bcompare\b",
    r";",
    r",\s*(but|and|also)\s+",
    r",\s+(?=[A-Z])",
    r"\babout\b",
    r"publishing\s+about",
    r"\bresearch\s+(?:in|on|about)\s+\w+",
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


ROUTING_CACHE_TTL = 60.0
_routing_cache: dict[str, tuple[str, float, float]] = {}
_routing_cache_timestamps: dict[str, float] = {}


def _get_cached_routing(query: str) -> Optional[tuple[str, float, float]]:
    """Get cached routing decision if still valid. Returns (intent, confidence, stage)."""
    cache_key = hashlib.md5(query.lower().encode()).hexdigest()
    if cache_key in _routing_cache:
        timestamp = _routing_cache_timestamps.get(cache_key, 0)
        if time_module.time() - timestamp < ROUTING_CACHE_TTL:
            intent, confidence, stage = _routing_cache[cache_key]
            return intent, confidence, stage
        else:
            _routing_cache.pop(cache_key, None)
            _routing_cache_timestamps.pop(cache_key, None)
    return None


def _cache_routing_decision(query: str, intent: str, confidence: float, stage: float):
    """Cache a routing decision for 60 seconds."""
    cache_key = hashlib.md5(query.lower().encode()).hexdigest()
    _routing_cache[cache_key] = (intent, confidence, stage)
    _routing_cache_timestamps[cache_key] = time_module.time()


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
        self.self_calibration_data: list[JSONDict] = []

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
            self.self_calibration_data.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "intent": intent,
                    "confidence": confidence,
                    "was_correct": was_correct,
                }
            )
            if len(self.self_calibration_data) > 1000:
                self.self_calibration_data = self.self_calibration_data[-500:]

    def get_metrics(self) -> JSONDict:
        """Get current routing metrics."""
        avg_confidence = self.confidence_sum / self.total_routes if self.total_routes > 0 else 0.0
        return {
            "total_routes": self.total_routes,
            "route_distribution": self.route_distribution,
            "avg_confidence": round(avg_confidence, 3),
            "ambiguity_rate": round(self.ambiguity_rate, 3),
            "llm_enhancement_rate": round(self.llm_enhancement_count / self.total_routes, 3)
            if self.total_routes > 0
            else 0.0,
            "self_calibration_samples": len(self.self_calibration_data),
        }

    def recalibrate_confidence(self, intent: str, observed_accuracy: float) -> dict[str, Any]:
        """Recalibrate confidence thresholds based on observed accuracy."""
        if len(self.self_calibration_data) < 10:
            return {}

        recent_data = [d for d in self.self_calibration_data[-100:] if d["intent"] == intent]
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
    issues: list[str] = []
    query_lower = query.lower()
    for pattern in AMBIGUITY_PATTERNS:
        match = re.search(pattern, query_lower)
        if match:
            issues.append(match.group(0))
    return len(issues) > 0, issues


def _detect_multi_intent(query: str) -> tuple[bool, list[str]]:
    """Detect if query contains multiple intents that need decomposition."""
    subqueries: list[str] = []
    query_lower = query.lower()

    SHORT_ACCEPTABLE_PREFIXES = (
        "recently",
        "currently",
        "today",
        "now",
        "latest",
        "historically",
        "recent",
        "past",
    )

    for separator in MULTI_INTENT_SEPARATORS:
        parts = re.split(separator, query_lower, maxsplit=2, flags=re.IGNORECASE)
        if len(parts) > 1:
            for part in parts:
                part = part.strip()
                if len(part) > 10 or part.startswith(SHORT_ACCEPTABLE_PREFIXES):
                    subqueries.append(part)

    if len(subqueries) < 2:
        sentences = re.split(r"[?;]", query_lower)
        valid_subqueries = [s.strip() for s in sentences if len(s.strip()) > 20]
        if len(valid_subqueries) > 1:
            subqueries = valid_subqueries

    return len(subqueries) >= 2, subqueries


def _classify_intent_with_confidence(query: str) -> tuple[str, float, JSONDict]:
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
        return (
            "hybrid",
            confidence,
            {
                "scores": scores,
                "matched_patterns": matched_patterns["hybrid"],
                "reason": "hybrid keywords combined with structured/unstructured",
            },
        )

    if max_score == 0:
        return (
            "unstructured",
            0.5,
            {
                "scores": scores,
                "matched_patterns": [],
                "reason": "no patterns matched, defaulting to unstructured",
            },
        )

    confidence = min(0.9, 0.4 + (max_score * 0.2) + (total_matches * 0.05))

    tie_winner = None
    for intent in ("unstructured", "structured", "hybrid"):
        if scores[intent] == max_score:
            tie_winner = intent
            break

    if tie_winner:
        return (
            tie_winner,
            confidence,
            {
                "scores": scores,
                "matched_patterns": matched_patterns[tie_winner],
                "reason": f"highest score ({max_score}) for {tie_winner}",
            },
        )

    return (
        "unstructured",
        0.5,
        {
            "scores": scores,
            "matched_patterns": [],
            "reason": "fallback",
        },
    )


def _route_to_skill(intent: str) -> str:
    """Map intent to skill execution."""
    routing_map = {
        "structured": "text_to_sql",
        "unstructured": "rag",
        "hybrid": "text_to_sql+rag",
    }
    return routing_map.get(intent, "rag")


def _apply_tier_complexity_limit(complexity: str, user_tier: int) -> tuple[str, str, bool]:
    """Clamp expensive query handling by tier before synthesis/provider selection."""
    limit = TIER_COMPLEXITY_LIMITS.get(user_tier, "moderate")
    try:
        if COMPLEXITY_ORDER.index(complexity) > COMPLEXITY_ORDER.index(limit):
            return limit, limit, True
    except ValueError:
        return limit, limit, True
    return complexity, limit, False


INTENT_CLASSIFICATION_PROMPT = """You are an expert intent classifier for a national research graph query system.

Classify this query as EXACTLY ONE of three intents:
- text_to_sql (structured): The query asks for specific database data — counts, lists, rankings, facts about researchers, publications, labs, funding, institutions. Examples: "list researchers in Gujarat", "count publications in 2023", "show funding for AI projects", "which labs have the most publications"
- rag (unstructured): The query asks for understanding, explanations, descriptions, trends, or analysis from research documents. Examples: "what are trends in AI research", "explain hydrogen catalysis breakthroughs", "summarize research directions", "describe recent advances"
- text_to_sql+rag (hybrid): The query clearly needs BOTH structured database data AND document analysis. Examples: "find researchers in ML and explain their recent work", "list top funded projects and analyze their impact", "what papers did top researchers publish and what are they about"

Query: "{query}"

Stage 1 analysis: intent={stage1_intent}, confidence={stage1_confidence:.2f}

Respond with ONLY JSON: {{"route": "text_to_sql" | "rag" | "text_to_sql+rag", "confidence": 0.0-1.0, "reasoning": "brief explanation"}}
"""


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


def _classify_intent_via_llm(
    query: str, stage1_intent: str, stage1_confidence: float
) -> tuple[Optional[str], float]:
    """Classify intent using Minimax LLM (primary) or local LLM (fallback).

    Args:
        query: The user query
        stage1_intent: The intent from regex classification
        stage1_confidence: The confidence from regex classification

    Returns:
        tuple: (resolved_intent, llm_confidence) or (None, 0.0) if LLM unavailable
    """
    cached = _get_cached_routing(query)
    if cached:
        logger.info("Routing cache hit for: %s", query[:50])
        return cached[0], cached[1]

    def _call_llm() -> tuple[Optional[str], float]:
        try:
            from src.config.llm_config import get_llm_client

            client = get_llm_client("minimax")
            if client is None:
                try:
                    from src.config.local_llm import get_local_llm_client

                    client = get_local_llm_client()
                except ImportError:
                    return None, 0.0
            if client is None:
                return None, 0.0
            llm_client = cast(RouterLLM, client)

            prompt = INTENT_CLASSIFICATION_PROMPT.format(
                query=query,
                stage1_intent=stage1_intent,
                stage1_confidence=stage1_confidence,
            )
            response = llm_client.generate(
                system_prompt="You are an expert research query classifier. Return ONLY valid JSON.",
                user_prompt=prompt,
                conversation_history=[],
            )

            data = _as_json_dict(json.loads(response))
            route = data.get("route", "")
            confidence = float(data.get("confidence", 0.8))

            route_map = {
                "text_to_sql": "structured",
                "rag": "unstructured",
                "text_to_sql+rag": "hybrid",
            }
            intent = route_map.get(route, stage1_intent)
            if intent not in ("structured", "unstructured", "hybrid"):
                intent = stage1_intent

            logger.info(
                "LLM intent classification: %s -> %s (conf %.2f, stage1=%s)",
                query[:50],
                intent,
                confidence,
                stage1_intent,
            )
            return intent, confidence

        except (json.JSONDecodeError, KeyError, ValueError, TypeError) as e:
            logger.warning("LLM classification parse failed: %s", e)
            return None, 0.0
        except Exception as e:
            logger.warning("LLM intent classification failed: %s", e)
            return None, 0.0

    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_call_llm)
            intent, confidence = future.result(timeout=2.0)
    except (FuturesTimeoutError, ImportError, OSError):
        logger.warning("LLM classification timed out after 2s, using stage1 result")
        return None, 0.0

    if intent:
        _cache_routing_decision(query, intent, confidence, 2.0)

    return intent, confidence


def decompose_intent_via_llm(query: str) -> list[str]:
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
        llm_client = cast(RouterLLM, client)

        prompt = MULTI_INTENT_DECOMPOSITION_PROMPT.format(query=query)
        response = llm_client.generate(
            system_prompt="You are a query decomposer. Return ONLY a JSON array of strings.",
            user_prompt=prompt,
            conversation_history=[],
        )

        try:
            subqueries = _as_string_list(json.loads(response))
            if subqueries:
                logger.info("LLM decomposed query into %d sub-queries", len(subqueries))
                return subqueries
        except json.JSONDecodeError:
            match = re.search(r"\[.*\]", response, re.DOTALL)
            if match:
                subqueries = _as_string_list(json.loads(match.group(0)))
                if subqueries:
                    return subqueries

        return [query]
    except Exception as e:
        logger.warning("LLM intent decomposition failed: %s", e)
        return [query]


def _apply_default_clarifications(query: str) -> list[str]:
    """Apply default clarifications for ambiguous terms."""
    clarifications: list[str] = []
    query_lower = query.lower()

    if "best" in query_lower or "top" in query_lower:
        clarifications.append("Assumption: 'best' = most publications in last 5 years")
    if "compare" in query_lower or "versus" in query_lower or " vs " in query_lower:
        clarifications.append("Assumption: compare = publication count and funding")
    if "recent" in query_lower or "currently" in query_lower or "lately" in query_lower:
        current_year = datetime.now().year
        years_ago = current_year - 3
        clarifications.append(f"Assumption: 'recent' = last 3 years ({years_ago}-{current_year})")
    if "leading" in query_lower or "strongest" in query_lower:
        clarifications.append("Assumption: 'leading' = highest h-index score")

    return clarifications


def _intent_for_catalog_route(route: str) -> str:
    if route == "text_to_sql":
        return "structured"
    if route == "rag":
        return "unstructured"
    return "hybrid"


def _catalog_should_short_circuit(classification: QueryClassification) -> bool:
    if classification.route in {"blocked", "clarify"}:
        return True
    return (
        bool(classification.matched_tables)
        and classification.confidence >= CONFIDENCE_THRESHOLD_HIGH
    )


def _catalog_routing_result(
    classification: QueryClassification,
    user_query: str,
    user_tier: int,
) -> JSONDict:
    detected_ambiguous, detected_issues = _detect_ambiguity(user_query)
    ambiguity_is_resolved = _catalog_resolves_ambiguity(user_query, detected_issues)
    intent = _intent_for_catalog_route(classification.route)
    routing_decision = classification.route
    if (
        detected_ambiguous
        and not ambiguity_is_resolved
        and classification.route not in {"blocked", "clarify", "text_to_sql+rag"}
    ):
        intent = "hybrid"
        routing_decision = "text_to_sql+rag"
    confidence = classification.confidence
    is_ambiguous = classification.needs_clarification or (
        detected_ambiguous and not ambiguity_is_resolved
    )
    ambiguity_issues: list[str] = ["needs_clarification"] if classification.needs_clarification else []
    if is_ambiguous:
        ambiguity_issues.extend(detected_issues)
    clarifications: list[str] = []
    if classification.clarification_question:
        clarifications.append(classification.clarification_question)
    if is_ambiguous:
        clarifications.extend(_apply_default_clarifications(user_query))

    rationale = [
        "Stage: catalog",
        f"Intent: {intent}",
        f"Confidence: {confidence:.2f}",
        f"Catalog route: {routing_decision}",
        f"Matched tables: {list(classification.matched_tables)}",
        f"Matched domains: {list(classification.matched_domains)}",
    ]
    rationale.extend(classification.rationale)

    try:
        from src.orchestration.nodes.complexity_classifier import get_complexity_for_routing

        complexity_result = get_complexity_for_routing(user_query, user_tier)
        complexity = complexity_result.level.value
    except Exception:
        complexity = "moderate"

    complexity, complexity_limit, complexity_limit_applied = _apply_tier_complexity_limit(
        complexity,
        user_tier,
    )
    if complexity_limit_applied:
        rationale.append(
            f"Tier complexity limit: capped to {complexity_limit} for tier {user_tier}"
        )

    return {
        "intent": intent,
        "routing_decision": routing_decision,
        "routing_confidence": confidence,
        "routing_rationale": rationale,
        "routing_reason": "; ".join(classification.rationale)
        or f"Catalog routed to {routing_decision}",
        "plan_skills_used": False,
        "multi_intent": False,
        "subqueries": [],
        "is_ambiguous": is_ambiguous,
        "ambiguity_issues": ambiguity_issues,
        "clarifications": clarifications,
        "llm_enhanced": False,
        "stage": "catalog",
        "catalog_route": classification.route,
        "catalog_confidence": classification.confidence,
        "catalog_matches": list(classification.matched_tables),
        "matched_domains": list(classification.matched_domains),
        "needs_clarification": classification.needs_clarification,
        "clarification_question": classification.clarification_question,
        "blocked_reason": classification.blocked_reason,
        "pii_terms": list(classification.pii_terms),
        "complexity": complexity,
        "complexity_limit": complexity_limit,
        "complexity_limit_applied": complexity_limit_applied,
    }


def _catalog_resolves_ambiguity(user_query: str, ambiguity_issues: list[str]) -> bool:
    if not ambiguity_issues:
        return True
    lowered = user_query.lower()
    ranking_issues = {"best", "top", "leading", "most", "strongest", "greatest"}
    if set(ambiguity_issues).issubset(ranking_issues):
        return any(
            marker in lowered
            for marker in (
                " by ",
                "total ",
                "amount",
                "count",
                "number of",
                "citation",
                "grant amount",
                "year",
            )
        )
    return False


def _stage1_regex_classification(
    user_query: str,
) -> tuple[str, float, JSONDict, bool, list[str]]:
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

    clarifications: list[str] = []
    llm_enhanced = False

    if is_ambiguous or confidence < CONFIDENCE_THRESHOLD_HIGH:
        llm_result = _classify_intent_via_llm(user_query, intent, confidence)
        llm_intent, llm_confidence = _coerce_llm_route_result(llm_result, confidence)
        if llm_intent:
            resolved_intent = llm_intent
            resolved_confidence = max(llm_confidence, confidence + 0.05)
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

    if is_ambiguous and confidence < CONFIDENCE_THRESHOLD_HIGH:
        clarifications = _apply_default_clarifications(user_query)
        if intent != "hybrid":
            return "hybrid", 0.75, True, ambiguity_issues, clarifications, llm_enhanced

    if is_ambiguous and not clarifications:
        clarifications = _apply_default_clarifications(user_query)

    if is_ambiguous and intent != "hybrid":
        intent = "hybrid"
        confidence = max(confidence, 0.75)
        if not clarifications:
            clarifications = _apply_default_clarifications(user_query)

    return intent, confidence, is_ambiguous, ambiguity_issues, clarifications, llm_enhanced


def _coerce_llm_route_result(result: Any, fallback_confidence: float) -> tuple[Optional[str], float]:
    """Normalize legacy string and current tuple/dict LLM route results."""
    if isinstance(result, str):
        intent = result if result in ("structured", "unstructured", "hybrid") else None
        return intent, max(fallback_confidence, CONFIDENCE_THRESHOLD_LOW)

    raw_intent: Any
    raw_confidence: Any
    if isinstance(result, Mapping):
        result_map = cast(Mapping[str, Any], result)
        raw_intent = result_map.get("intent") or result_map.get("route")
        raw_confidence = result_map.get("confidence", fallback_confidence)
    elif isinstance(result, (tuple, list)):
        result_sequence = cast(Sequence[Any], result)
        raw_intent = result_sequence[0] if len(result_sequence) > 0 else None
        raw_confidence = result_sequence[1] if len(result_sequence) > 1 else fallback_confidence
    else:
        return None, fallback_confidence

    route_map = {
        "text_to_sql": "structured",
        "rag": "unstructured",
        "text_to_sql+rag": "hybrid",
        "structured": "structured",
        "unstructured": "unstructured",
        "hybrid": "hybrid",
    }
    normalized_intent = route_map.get(str(raw_intent or ""))
    try:
        normalized_confidence = float(raw_confidence)
    except (TypeError, ValueError):
        normalized_confidence = fallback_confidence

    return normalized_intent, normalized_confidence


def router_node(state: Any) -> JSONDict:
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

    plan = _as_json_dict(_state_get(state, "plan", {}))

    desired_skills = _as_string_list(plan.get("desired_skills", []))
    if desired_skills:
        desired = {skill.lower() for skill in desired_skills}
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

    user_query = str(_state_get(state, "user_query", "") or "")

    user_tier = int(_state_get(state, "user_tier", 1) or 1)

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

    catalog_classification = classify_query(user_query, user_tier=user_tier)
    if _catalog_should_short_circuit(catalog_classification):
        result = _catalog_routing_result(catalog_classification, user_query, user_tier)
        metrics.record(
            str(result["intent"]),
            float(result["routing_confidence"]),
            bool(result["is_ambiguous"]),
            False,
        )
        return result

    is_multi_intent, subqueries = _detect_multi_intent(user_query)

    intent, confidence, details, is_ambiguous, ambiguity_issues = _stage1_regex_classification(
        user_query
    )

    if ENABLE_2STAGE_ROUTING and (is_ambiguous or confidence < CONFIDENCE_THRESHOLD_HIGH):
        intent, confidence, is_ambiguous, ambiguity_issues, clarifications, llm_enhanced = (
            _stage2_llm_confirmation(user_query, intent, confidence, is_ambiguous, ambiguity_issues)
        )
        details["stage"] = "llm"
    else:
        clarifications = []
        llm_enhanced = False
        if is_ambiguous:
            clarifications = _apply_default_clarifications(user_query)
            if intent != "hybrid":
                intent = "hybrid"
                confidence = max(confidence, 0.75)

    if is_multi_intent and intent != "hybrid":
        logger.info("Multi-intent detected, upgrading to hybrid")
        intent = "hybrid"
        confidence = max(confidence, 0.75)
        if not clarifications:
            clarifications = ["Multi-intent query, using hybrid for comprehensive answer"]

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

    reasoning_parts: list[str] = []
    matched_patterns = _as_string_list(details.get("matched_patterns", []))
    if matched_patterns:
        reasoning_parts.append(f"Patterns: {', '.join(matched_patterns[:3])}")
    if is_ambiguous:
        reasoning_parts.append(f"Ambiguity detected: {', '.join(ambiguity_issues[:2])}")
    if llm_enhanced:
        reasoning_parts.append("LLM confirmed classification")
    if is_multi_intent:
        reasoning_parts.append(f"Multi-intent: {len(subqueries)} sub-queries identified")
    if confidence < CONFIDENCE_THRESHOLD_LOW:
        reasoning_parts.append("Low confidence threshold triggered hybrid fallback")
    reasoning_parts.append(f"Route: {intent} via {routing_decision}")

    routing_reason = (
        "; ".join(reasoning_parts)
        if reasoning_parts
        else f"{intent.title()} query routed to {routing_decision}"
    )

    rationale: list[str] = [
        f"Stage: {details.get('stage', 'unknown')}",
        f"Intent: {intent}",
        f"Confidence: {confidence:.2f}",
        f"Threshold check: {'PASS' if confidence >= CONFIDENCE_THRESHOLD_LOW else 'FAIL (forced hybrid)'}",
        f"Matched patterns: {matched_patterns}",
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

    try:
        from src.orchestration.nodes.complexity_classifier import get_complexity_for_routing

        complexity_result = get_complexity_for_routing(user_query, user_tier)
        complexity = complexity_result.level.value
    except Exception:
        complexity = "moderate"

    complexity, complexity_limit, complexity_limit_applied = _apply_tier_complexity_limit(
        complexity,
        user_tier,
    )
    if complexity_limit_applied:
        rationale.append(
            f"Tier complexity limit: capped to {complexity_limit} for tier {user_tier}"
        )
        reasoning_parts.append(f"Complexity capped to {complexity_limit}")

    return {
        "intent": intent,
        "routing_decision": routing_decision,
        "routing_confidence": confidence,
        "routing_rationale": rationale,
        "routing_reason": routing_reason,
        "plan_skills_used": False,
        "multi_intent": is_multi_intent,
        "subqueries": subqueries if is_multi_intent else [],
        "is_ambiguous": is_ambiguous,
        "ambiguity_issues": ambiguity_issues,
        "clarifications": clarifications,
        "llm_enhanced": llm_enhanced,
        "stage": details.get("stage", "regex"),
        "complexity": complexity,
        "complexity_limit": complexity_limit,
        "complexity_limit_applied": complexity_limit_applied,
    }
