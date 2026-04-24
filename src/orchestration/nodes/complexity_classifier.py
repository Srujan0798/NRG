"""Complexity Classifier — Protocol #38: Complexity Router.

Classifies each query by complexity level to route to appropriate LLM provider:

- trivial: rule-based / no LLM needed
- simple: single-table lookup, smallest model
- moderate: multi-table join, standard model
- complex: multi-hop reasoning, cloud LLM + parallel racing
- synthesis-heavy: DAG planning + multi-source, strongest model

The classifier uses keyword analysis + structural heuristics. For production,
an LLM-based classifier can be swapped in.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ComplexityLevel(Enum):
    TRIVIAL = "trivial"
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    SYNTHESIS_HEAVY = "synthesis_heavy"


COMPLEXITY_DESCRIPTIONS = {
    ComplexityLevel.TRIVIAL: "No LLM needed — rule-based or keyword search",
    ComplexityLevel.SIMPLE: "Single-table lookup — smallest/fastest model",
    ComplexityLevel.MODERATE: "Multi-table — standard model",
    ComplexityLevel.COMPLEX: "Multi-hop reasoning — cloud LLM + parallel racing",
    ComplexityLevel.SYNTHESIS_HEAVY: "DAG planning + multi-source — strongest model",
}


@dataclass
class ComplexityResult:
    level: ComplexityLevel
    confidence: float  # 0.0–1.0
    signals: list[str]  # keyword/pattern matches that contributed
    recommended_provider: str  # e.g., "local", "standard", "cloud"
    recommended_model: str  # e.g., "gpt-4o-mini", "claude-haiku", "gpt-4o"
    estimated_latency_ms: int  # approximate
    use_cache: bool  # True for simple/trivial


COMPLEXITY_PATTERNS = {
    ComplexityLevel.TRIVIAL: [
        (r"^(list|show|find|get)\s+\w+\s+(in|at|from)\s+\w+$", 0.9),  # "list researchers in Gujarat"
        (r"^(count|how many)\s+\w+\s+(in|at|from)\s+\w+$", 0.9),
        (r"^(who|what)\s+(is|are)\s+\w+\s*$", 0.85),
    ],
    ComplexityLevel.SIMPLE: [
        (r"(list|show|find|get|count).*(researcher|institution|lab|publication|project)", 0.7),
        (r"(how many|number of)", 0.6),
        (r"(top\s+\d+|best\s+\d+)", 0.6),
    ],
    ComplexityLevel.MODERATE: [
        (r"(compare|versus|vs|between).*(and|with)", 0.8),
        (r"(trend|over\s+time|history|last\s+\d+\s+year)", 0.75),
        (r"(aggregate|sum|average|total|group\s+by)", 0.7),
        (r"(join|combine).*(with|together)", 0.7),
    ],
    ComplexityLevel.COMPLEX: [
        (r"(synthesize|integrate|correlat)", 0.9),
        (r"(why|explain|analyze).*(reason|cause|impact)", 0.8),
        (r"(research\w*|fund\w*|output\w*).*(gap|trends?|comparison)", 0.85),
        (r"(cross|multi).*(domain|table|hierarchy)", 0.8),
        (r"(complex|advanced).*(query|search|analysis)", 0.8),
    ],
    ComplexityLevel.SYNTHESIS_HEAVY: [
        (r"(synthesis|synthesize)", 0.95),
        (r"(comprehensive|full|complete).*(analysis|overview|summary)", 0.9),
        (r"(research\w*|fund\w*|output\w*).*(gap|trends?|comparison).*(and|with)", 0.9),
        (r"(multi.?hop|chain|reasoning|dag|decomposition)", 0.95),
        (r"(artificial\s+intelligence|machine\s+learning|ai\s+and\s+\w+)", 0.8),
    ],
}

PROVIDER_RECOMMENDATIONS = {
    ComplexityLevel.TRIVIAL: ("none", "rule_based", 10),
    ComplexityLevel.SIMPLE: ("local", "gpt-4o-mini", 2000),
    ComplexityLevel.MODERATE: ("cloud", "claude-haiku-4", 5000),
    ComplexityLevel.COMPLEX: ("cloud", "gpt-4o", 10000),
    ComplexityLevel.SYNTHESIS_HEAVY: ("cloud", "claude-sonnet-4", 15000),
}

QUERY_TYPE_KEYWORDS = {
    "lookup": ["find", "list", "show", "get", "who", "what"],
    "aggregation": ["count", "sum", "average", "total", "how many", "number of"],
    "comparison": ["compare", "versus", "vs", "difference", "gap", "between"],
    "time_series": ["trend", "over time", "history", "last year", "growth", "decline"],
    "top_n": ["top", "best", "highest", "lowest", "ranked"],
    "cross_domain": ["and", "with", "combine", "integrate", "synthesis"],
}


def classify_complexity(query: str, user_tier: int = 1) -> ComplexityResult:
    """Classify query complexity using keyword + pattern analysis."""
    query_lower = query.lower()
    tokens = set(re.findall(r'\w+', query_lower))

    scores: dict[ComplexityLevel, float] = {level: 0.0 for level in ComplexityLevel}
    signals: dict[ComplexityLevel, list[str]] = {level: [] for level in ComplexityLevel}

    for level, patterns in COMPLEXITY_PATTERNS.items():
        for pattern, weight in patterns:
            if re.search(pattern, query_lower, re.IGNORECASE):
                scores[level] += weight
                signals[level].append(re.search(pattern, query_lower, re.IGNORECASE).group(0))

    dag_indicators = ["compare", "and", "gap", "versus", "synthesis", "both", "funding", "output"]
    if sum(1 for ind in dag_indicators if ind in query_lower) >= 3:
        scores[ComplexityLevel.COMPLEX] += 0.5
        scores[ComplexityLevel.SYNTHESIS_HEAVY] += 0.4

    multi_table_indicators = ["researcher", "publication", "institution", "lab", "funding", "patent"]
    table_count = sum(1 for t in multi_table_indicators if t in query_lower)
    if table_count >= 3:
        scores[ComplexityLevel.COMPLEX] += 0.5
        scores[ComplexityLevel.SYNTHESIS_HEAVY] += 0.3

    if len(query.split()) > 30:
        scores[ComplexityLevel.COMPLEX] += 0.3
        scores[ComplexityLevel.SYNTHESIS_HEAVY] += 0.2

    best_level = max(scores, key=lambda l: scores[l])
    best_score = scores[best_level]

    if best_score < 0.5:
        if scores[ComplexityLevel.SIMPLE] >= 0.3:
            best_level = ComplexityLevel.SIMPLE
            best_score = scores[ComplexityLevel.SIMPLE]
        else:
            best_level = ComplexityLevel.TRIVIAL
            best_score = 1.0

    provider, model, latency = PROVIDER_RECOMMENDATIONS[best_level]
    confidence = min(best_score, 1.0)

    query_type = _detect_query_type(query_lower)

    return ComplexityResult(
        level=best_level,
        confidence=round(confidence, 3),
        signals=sorted(set(signals[best_level])),
        recommended_provider=provider,
        recommended_model=model,
        estimated_latency_ms=latency,
        use_cache=best_level in (ComplexityLevel.TRIVIAL, ComplexityLevel.SIMPLE),
    )


def _detect_query_type(query_lower: str) -> str:
    """Detect primary query type from keywords."""
    type_scores: dict[str, float] = {}
    for qtype, keywords in QUERY_TYPE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in query_lower)
        if score > 0:
            type_scores[qtype] = score
    if not type_scores:
        return "lookup"
    return max(type_scores, key=type_scores.get)


def get_complexity_for_routing(query: str, user_tier: int = 1) -> ComplexityResult:
    """Main entry point for routing decisions."""
    return classify_complexity(query, user_tier)


def compute_query_fingerprint(query: str, user_tier: int = 1) -> str:
    """Compute a stable cache key fingerprint for a query.

    Uses normalized query text (lowercase, stripped) and user_tier
    to produce a SHA256 hash truncated to 32 characters.
    """
    import hashlib
    normalized = query.strip().lower()
    raw = f"{normalized}|tier={user_tier}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]
