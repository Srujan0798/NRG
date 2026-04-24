"""
Training Data Quality Filter — Task #22 Phase 2
Grades each captured pair as GOLD/SILVER/BRONZE/REJECT.
Removes REJECT pairs, deduplicates by cosine similarity.
"""

from __future__ import annotations

import logging
import math
import re
from typing import Any

logger = logging.getLogger(__name__)

GRADE_THRESHOLDS = {
    "gold": {"verifier_score_min": 0.8, "latency_ms_max": 5000, "min_row_count": 1},
    "silver": {"verifier_score_min": 0.5, "min_response_length": 100},
    "bronze": {"verifier_score_min": 0.0, "min_response_length": 1},
}


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    if not vec1 or not vec2:
        return 0.0
    dot = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


def _estimate_query_embedding(query: str) -> list[float]:
    """Simple TF-based embedding for deduplication (no model needed).

    Uses word frequency as a proxy for embedding.
    Production: replace with actual embedding model.
    """
    words = re.findall(r"\w+", query.lower())
    if not words:
        return [0.0] * 100
    freq: dict[str, float] = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    max_freq = max(freq.values()) if freq else 1
    vec = [0.0] * 100
    for i, w in enumerate(words[:100]):
        vec[i % 100] += freq[w] / max_freq
    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec


class QualityFilter:
    """Filters and grades training pairs for fine-tuning quality.

    Grading:
    - GOLD: verifier_score > 0.8 AND latency < 5s AND SQL returned rows
    - SILVER: verifier_score > 0.5 AND response > 100 chars
    - BRONZE: generated a response (any length)
    - REJECT: verifier failed, SQL error, empty response, or PII detected

    Deduplication: removes pairs where cosine similarity > 0.95.
    """

    def __init__(
        self,
        similarity_threshold: float = 0.95,
        min_response_length: int = 10,
    ):
        self.similarity_threshold = similarity_threshold
        self.min_response_length = min_response_length
        self._seen_embeddings: list[tuple[list[float], str]] = []

    def grade_pair(self, pair: dict[str, Any]) -> str:
        """Grade a single training pair."""
        route = pair.get("route", "unknown")
        verifier_score = float(pair.get("verifier_score", 0.0) or 0.0)
        latency_ms = int(pair.get("latency_ms", 0) or 0)
        response = str(pair.get("response") or "")
        sql_row_count = int(pair.get("sql_row_count", 0) or 0)
        sql_error = pair.get("sql_result", "")

        if not response or len(response.strip()) < self.min_response_length:
            return "reject"
        if "error" in sql_error.lower() and route == "text_to_sql":
            return "reject"
        if pair.get("pii_scrubbed") is False:
            return "reject"
        if route == "text_to_sql" and sql_row_count == 0 and len(response) < 50:
            return "reject"

        if (
            verifier_score > GRADE_THRESHOLDS["gold"]["verifier_score_min"]
            and latency_ms < GRADE_THRESHOLDS["gold"]["latency_ms_max"]
            and sql_row_count >= GRADE_THRESHOLDS["gold"]["min_row_count"]
        ):
            return "gold"

        if (
            verifier_score > GRADE_THRESHOLDS["silver"]["verifier_score_min"]
            and len(response) >= GRADE_THRESHOLDS["silver"]["min_response_length"]
        ):
            return "silver"

        if verifier_score > 0 or len(response) > 0:
            return "bronze"

        return "reject"

    def filter_pairs(self, pairs: list[dict[str, Any]]) -> tuple[list[dict], dict]:
        """Filter and deduplicate a list of training pairs.

        Returns (kept_pairs, stats_dict).
        """
        if not pairs:
            return [], {"total": 0, "gold": 0, "silver": 0, "bronze": 0, "reject": 0, "dedup_removed": 0}

        graded = []
        stats = {"total": len(pairs), "gold": 0, "silver": 0, "bronze": 0, "reject": 0, "dedup_removed": 0}

        for pair in pairs:
            grade = self.grade_pair(pair)
            pair["quality_grade"] = grade
            graded.append(pair)
            stats[grade] = stats.get(grade, 0) + 1

        non_reject = [p for p in graded if p.get("quality_grade") != "reject"]

        deduped: list[dict] = []
        for pair in non_reject:
            query = pair.get("query", "")
            emb = _estimate_query_embedding(query)
            is_dup = False
            for seen_emb, _ in self._seen_embeddings:
                sim = cosine_similarity(emb, seen_emb)
                if sim > self.similarity_threshold:
                    is_dup = True
                    stats["dedup_removed"] += 1
                    break
            if not is_dup:
                self._seen_embeddings.append((emb, query))
                deduped.append(pair)

        return deduped, stats

    def filter_batch(self, pairs: list[dict[str, Any]]) -> list[dict]:
        """Filter pairs: remove REJECT, deduplicate, re-grade."""
        filtered, _ = self.filter_pairs(pairs)
        return filtered

    def get_export_grade_filter(self, min_grade: str = "silver") -> set[str]:
        """Return the set of grades suitable for export."""
        grade_order = ["gold", "silver", "bronze", "reject", "ungraded"]
        if min_grade not in grade_order:
            min_grade = "silver"
        cutoff = grade_order.index(min_grade)
        return set(grade_order[:cutoff + 1])


def regrade_pair(
    verifier_score: float,
    latency_ms: int,
    sql_row_count: int,
    response_length: int,
    route: str,
) -> str:
    """Re-grade a pair using current thresholds. Utility function."""
    if route == "text_to_sql" and sql_row_count == 0:
        return "reject"
    if verifier_score > 0.8 and latency_ms < 5000 and sql_row_count > 0:
        return "gold"
    if verifier_score > 0.5 and response_length > 100:
        return "silver"
    if verifier_score > 0 or response_length > 0:
        return "bronze"
    return "reject"
