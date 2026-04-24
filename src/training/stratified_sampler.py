"""
Stratified Sampler — Protocol #40: Stratified Curator for NRG

Applies stratified sampling to training pair exports to prevent model
overfitting to majority query type (simple lookups). Balances across:
- Tiers (Tier 1/2/3)
- Routes (sql/rag/hybrid)
- Query types (lookup/aggregation/comparison/time_series/top_n/cross_domain)
- Quality grades (gold/silver/bronze)

Output: balanced subset meeting all min thresholds.
"""

from __future__ import annotations

import random
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional


def _keyword_match(text: str, keywords: list[str]) -> int:
    """Count keyword matches using word boundaries."""
    count = 0
    for kw in keywords:
        if re.search(r'\b' + re.escape(kw) + r'\b', text, re.IGNORECASE):
            count += 1
    return count


QUERY_TYPE_KEYWORDS = {
    "lookup": ["find", "list", "show", "get", "who", "what"],
    "aggregation": ["count", "sum", "average", "total", "how many", "number of"],
    "comparison": ["compare", "versus", "vs", "difference", "gap", "between"],
    "time_series": ["trend", "over time", "history", "last year", "growth", "decline"],
    "top_n": ["top", "best", "highest", "lowest", "ranked"],
    "cross_domain": ["combine", "integrate", "integration", "synthesis", "cross"],
}


@dataclass
class SamplingConfig:
    min_tier1: int = 50
    min_tier2: int = 30
    min_tier3: int = 20
    min_per_route: int = 20
    min_per_query_type: int = 10
    min_per_grade: int = 10
    max_total: int = 10000
    oversample_if_needed: bool = False


@dataclass
class StratificationConfig:
    target_size: int = 5000
    min_per_stratum: int = 20
    random_seed: int = 42
    balance_tiers: bool = True
    balance_routes: bool = True
    balance_query_types: bool = True
    balance_grades: bool = True


class StratifiedSampler:
    """Stratified sampling for balanced fine-tuning exports.

    Ensures the exported dataset is representative across all dimensions
    rather than over-represented by the majority class.
    """

    def __init__(self, config: Optional[SamplingConfig] = None):
        self.config = config or SamplingConfig()

    def _classify_query_type(self, query: str) -> str:
        """Classify into: lookup, aggregation, comparison, time_series, top_n, cross_domain."""
        if not query:
            return "lookup"
        query_lower = query.lower()
        type_scores: dict[str, float] = {}
        for qtype, keywords in QUERY_TYPE_KEYWORDS.items():
            score = _keyword_match(query_lower, keywords)
            if score > 0:
                type_scores[qtype] = score
        if not type_scores:
            return "lookup"
        lookup_score = type_scores.get("lookup", 0)
        non_lookup_scores = {k: v for k, v in type_scores.items() if k != "lookup"}
        if non_lookup_scores:
            return max(non_lookup_scores, key=non_lookup_scores.get)
        return "lookup"

    def _get_tier(self, pair: dict) -> int:
        tier = pair.get("tier", pair.get("user_tier", 1))
        try:
            return int(tier)
        except (TypeError, ValueError):
            return 1

    def _get_tier_bucket(self, pair: dict) -> str:
        tier = self._get_tier(pair)
        if tier == 1:
            return "tier1"
        elif tier == 2:
            return "tier2"
        else:
            return "tier3"

    def _get_route(self, pair: dict) -> str:
        return pair.get("route", pair.get("skill", "unknown"))

    def _get_grade(self, pair: dict) -> str:
        return pair.get("quality_grade", "ungraded")

    def _get_query_type(self, pair: dict) -> str:
        qtype = pair.get("query_type", pair.get("intent"))
        if qtype:
            return qtype
        query = pair.get("query", pair.get("user_query", ""))
        return self._classify_query_type(query)

    def compute_diversity_profile(self, pairs: list[dict]) -> dict:
        """Returns breakdown: {tier: count, route: count, query_type: count, grade: count}."""
        if not pairs:
            return {"tier": {}, "route": {}, "query_type": {}, "grade": {}}

        profile = {
            "tier": defaultdict(int),
            "route": defaultdict(int),
            "query_type": defaultdict(int),
            "grade": defaultdict(int),
        }

        for p in pairs:
            profile["tier"][self._get_tier_bucket(p)] += 1
            profile["route"][self._get_route(p)] += 1
            profile["query_type"][self._get_query_type(p)] += 1
            profile["grade"][self._get_grade(p)] += 1

        return {
            "tier": dict(profile["tier"]),
            "route": dict(profile["route"]),
            "query_type": dict(profile["query_type"]),
            "grade": dict(profile["grade"]),
        }

    def stratify_pairs(self, pairs: list[dict]) -> list[dict]:
        """Apply stratified sampling to pairs list.

        Input: raw training pairs from DB
        Output: balanced subset meeting all min thresholds

        If a bucket has fewer than minimum, include ALL of them (don't fabricate data).
        If total would exceed max_total, proportionally reduce while maintaining ratios.
        """
        if not pairs:
            return []

        min_config = {
            "tier1": self.config.min_tier1,
            "tier2": self.config.min_tier2,
            "tier3": self.config.min_tier3,
            "route": self.config.min_per_route,
            "query_type": self.config.min_per_query_type,
            "grade": self.config.min_per_grade,
        }

        dim_buckets: dict[str, dict[str, list[dict]]] = {
            "tier": defaultdict(list),
            "route": defaultdict(list),
            "query_type": defaultdict(list),
            "grade": defaultdict(list),
        }

        for p in pairs:
            dim_buckets["tier"][self._get_tier_bucket(p)].append(p)
            dim_buckets["route"][self._get_route(p)].append(p)
            dim_buckets["query_type"][self._get_query_type(p)].append(p)
            dim_buckets["grade"][self._get_grade(p)].append(p)

        small_bucket_ids: set[str] = set()
        large_buckets: dict[str, list[dict]] = {}

        for dim, buckets in dim_buckets.items():
            min_threshold = min_config.get(dim, 10)
            for bucket_name, bucket_pairs in buckets.items():
                if len(bucket_pairs) < min_threshold:
                    for p in bucket_pairs:
                        pid = p.get("id", id(p))
                        small_bucket_ids.add(pid)
                else:
                    key = f"{dim}:{bucket_name}"
                    large_buckets[key] = bucket_pairs

        result_ids: set[str] = set()
        result: list[dict] = []

        for p in pairs:
            pid = p.get("id", id(p))
            if pid in small_bucket_ids and pid not in result_ids:
                result.append(p)
                result_ids.add(pid)

        total_large = sum(len(v) for v in large_buckets.values())
        budget = self.config.max_total - len(result)

        if total_large <= budget:
            for bucket_pairs in large_buckets.values():
                for p in bucket_pairs:
                    pid = p.get("id", id(p))
                    if pid not in result_ids:
                        result.append(p)
                        result_ids.add(pid)
            random.seed(42)
            random.shuffle(result)
            return result[:self.config.max_total]

        ratios = {k: len(v) / total_large for k, v in large_buckets.items()}

        for key, bucket_pairs in large_buckets.items():
            ratio = ratios[key]
            target_count = int(budget * ratio)
            target_count = max(target_count, 1)

            if self.config.oversample_if_needed:
                dim = key.split(":")[0]
                min_threshold = min_config.get(dim, 10)
                if target_count < min_threshold:
                    target_count = min(min_threshold, len(bucket_pairs) * 3)

            target_count = min(target_count, len(bucket_pairs))
            count = 0
            for p in bucket_pairs:
                if count >= target_count:
                    break
                pid = p.get("id", id(p))
                if pid not in result_ids:
                    result.append(p)
                    result_ids.add(pid)
                    count += 1

        random.seed(42)
        random.shuffle(result)
        return result[:self.config.max_total]

    def get_balanced_sample(self, pairs: list[dict], config: SamplingConfig) -> list[dict]:
        """Main entry point for balanced sampling."""
        self.config = config
        return self.stratify_pairs(pairs)


def get_balanced_sample(pairs: list[dict], config: SamplingConfig) -> list[dict]:
    """Main entry point for balanced sampling."""
    sampler = StratifiedSampler(config)
    return sampler.stratify_pairs(pairs)
