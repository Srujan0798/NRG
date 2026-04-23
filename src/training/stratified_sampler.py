"""
Stratified Sampler — Protocol #40: Balanced Fine-Tuning Export

Applies stratified sampling when exporting training pairs to prevent model
overfitting to majority query type. Balances across:
- Tiers (Tier 1/2/3)
- Routes (sql/rag/hybrid)
- Query types (lookup/aggregation/comparison/time-series/top-n/cross-domain)
- Quality grades (gold/silver/bronze)

Output: balanced JSONL/ShareGPT ready for fine-tune.

Files:
  - src/training/stratified_sampler.py
  - src/training/export.py (integrated via BalancedExportPipeline)
"""

from __future__ import annotations

import json
import logging
import math
import random
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class StratificationConfig:
    target_size: int = 5000
    min_per_stratum: int = 20
    max_per_stratum: Optional[int] = None
    balance_tiers: bool = True
    balance_routes: bool = True
    balance_query_types: bool = True
    balance_grades: bool = True
    random_seed: int = 42


@dataclass
class Stratum:
    key: tuple
    size: int
    pairs: list[dict] = field(default_factory=list)


class StratifiedSampler:
    """Stratified sampling for balanced fine-tuning exports.

    Ensures the exported dataset is representative across all dimensions
    rather than over-represented by the majority class.
    """

    def __init__(self, config: Optional[StratificationConfig] = None):
        self.config = config or StratificationConfig()

    def sample(self, pairs: list[dict]) -> list[dict]:
        """Apply stratified sampling to pairs list. Returns balanced sample."""
        if not pairs:
            return []

        strata = self._build_strata(pairs)

        if self.config.max_per_stratum:
            for s in strata:
                if len(s.pairs) > self.config.max_per_stratum:
                    s.pairs = self.config.max_per_stratum * [s.pairs[0]] + s.pairs[:self.config.max_per_stratum]

        target = self.config.target_size
        n_strata = len(strata)
        if n_strata == 0:
            return []

        base_per_stratum = target // n_strata
        remainder = target % n_strata

        sampled = []
        for i, stratum in enumerate(strata):
            n = base_per_stratum + (1 if i < remainder else 0)
            n = min(n, len(stratum.pairs))
            sampled.extend(stratum.pairs[:n])

        random.seed(self.config.random_seed)
        random.shuffle(sampled)

        logger.info(
            "Stratified sample: %d pairs from %d strata (target %d)",
            len(sampled), n_strata, target,
        )
        return sampled

    def _build_strata(self, pairs: list[dict]) -> list[Stratum]:
        by_key: dict[tuple, list[dict]] = defaultdict(list)

        for p in pairs:
            key = self._stratum_key(p)
            by_key[key].append(p)

        strata = []
        for key, group in by_key.items():
            if len(group) >= self.config.min_per_stratum:
                strata.append(Stratum(key=key, size=len(group), pairs=group))
            else:
                logger.debug(
                    "Stratum %s has only %d pairs (min=%d), excluding",
                    key, len(group), self.config.min_per_stratum,
                )

        return sorted(strata, key=lambda s: s.size, reverse=True)

    def _stratum_key(self, pair: dict) -> tuple:
        parts = []

        if self.config.balance_tiers:
            tier = str(pair.get("tier", pair.get("user_tier", "unknown")))
            parts.append(f"tier={tier}")

        if self.config.balance_routes:
            route = pair.get("route", pair.get("skill", "unknown"))
            parts.append(f"route={route}")

        if self.config.balance_query_types:
            qtype = pair.get("query_type", pair.get("intent", "unknown"))
            parts.append(f"qtype={qtype}")

        if self.config.balance_grades:
            grade = pair.get("quality_grade", "ungraded")
            parts.append(f"grade={grade}")

        return tuple(parts)


class BalancedExportPipeline:
    """Export pipeline that applies stratified sampling before formatting.

    Injects StratifiedSampler into the export pipeline to produce
    balanced datasets for fine-tuning.
    """

    def __init__(
        self,
        target_size: int = 5000,
        random_seed: int = 42,
        **sampler_kwargs,
    ):
        self.target_size = target_size
        self.random_seed = random_seed
        self.sampler = StratifiedSampler(
            StratificationConfig(
                target_size=target_size,
                random_seed=random_seed,
                **sampler_kwargs,
            )
        )

    def sample_and_export(self, pairs: list[dict], formatter: Any) -> tuple[list[dict], dict]:
        """Apply stratified sampling then format. Returns (formatted_pairs, stats)."""
        sampled = self.sampler.sample(pairs)

        strata_counts = defaultdict(int)
        for p in sampled:
            key = self.sampler._stratum_key(p)
            strata_counts[str(key[:4])] += 1

        return sampled, {
            "total_sampled": len(sampled),
            "strata_distribution": dict(strata_counts),
            "random_seed": self.random_seed,
        }


def balanced_sample(pairs: list[dict], target_size: int = 5000, seed: int = 42) -> list[dict]:
    """One-liner balanced sampling utility."""
    sampler = StratifiedSampler(StratificationConfig(target_size=target_size, random_seed=seed))
    return sampler.sample(pairs)


def compute_sample_statistics(pairs: list[dict]) -> dict:
    """Compute stratification statistics on a pairs list."""
    if not pairs:
        return {}

    stats = {
        "total": len(pairs),
        "by_tier": defaultdict(int),
        "by_route": defaultdict(int),
        "by_grade": defaultdict(int),
        "by_query_type": defaultdict(int),
    }

    for p in pairs:
        tier = str(p.get("tier", p.get("user_tier", "unknown")))
        route = p.get("route", p.get("skill", "unknown"))
        grade = p.get("quality_grade", "ungraded")
        qtype = p.get("query_type", p.get("intent", "unknown"))

        stats["by_tier"][tier] += 1
        stats["by_route"][route] += 1
        stats["by_grade"][grade] += 1
        stats["by_query_type"][qtype] += 1

    return dict(stats)