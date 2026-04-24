"""
Tests for StratifiedSampler — Protocol #40: Stratified Curator for NRG
"""

from src.training.stratified_sampler import (
    SamplingConfig,
    StratifiedSampler,
    get_balanced_sample,
    QUERY_TYPE_KEYWORDS,
)


class TestQueryTypeClassification:
    """Tests for _classify_query_type method."""

    def test_classifies_lookup(self):
        sampler = StratifiedSampler()
        assert sampler._classify_query_type("find researchers in Gujarat") == "lookup"
        assert sampler._classify_query_type("list institutions") == "lookup"
        assert sampler._classify_query_type("who is the professor") == "lookup"

    def test_classifies_aggregation(self):
        sampler = StratifiedSampler()
        assert sampler._classify_query_type("count of publications") == "aggregation"
        assert sampler._classify_query_type("sum of funding") == "aggregation"
        assert sampler._classify_query_type("how many researchers") == "aggregation"

    def test_classifies_comparison(self):
        sampler = StratifiedSampler()
        assert sampler._classify_query_type("compare institutions") == "comparison"
        assert sampler._classify_query_type("versus analysis") == "comparison"
        assert sampler._classify_query_type("gap between labs") == "comparison"

    def test_classifies_time_series(self):
        sampler = StratifiedSampler()
        assert sampler._classify_query_type("trend over time") == "time_series"
        assert sampler._classify_query_type("growth analysis last year") == "time_series"

    def test_classifies_top_n(self):
        sampler = StratifiedSampler()
        assert sampler._classify_query_type("top 10 researchers") == "top_n"
        assert sampler._classify_query_type("best ranked institutions") == "top_n"

    def test_classifies_cross_domain(self):
        sampler = StratifiedSampler()
        assert sampler._classify_query_type("combine researchers and publications") == "cross_domain"
        assert sampler._classify_query_type("integration with funding") == "cross_domain"

    def test_unknown_returns_lookup(self):
        sampler = StratifiedSampler()
        assert sampler._classify_query_type("random nonsense xyz") == "lookup"
        assert sampler._classify_query_type("") == "lookup"
        assert sampler._classify_query_type(None) == "lookup"

    def test_all_six_query_types_available(self):
        """Verify all 6 query types are defined in keywords."""
        assert set(QUERY_TYPE_KEYWORDS.keys()) == {
            "lookup",
            "aggregation",
            "comparison",
            "time_series",
            "top_n",
            "cross_domain",
        }


class TestStratifyPairs:
    """Tests for stratify_pairs method."""

    def test_stratify_enforces_minimums(self):
        """Small bucket included fully."""
        pairs = [
            {"id": "p1", "tier": 3, "route": "sql", "query_type": "lookup", "quality_grade": "gold", "query": "find researchers"},
            {"id": "p2", "tier": 3, "route": "sql", "query_type": "lookup", "quality_grade": "gold", "query": "list labs"},
            {"id": "p3", "tier": 3, "route": "sql", "query_type": "lookup", "quality_grade": "gold", "query": "get institutions"},
        ]
        config = SamplingConfig(min_tier3=2, min_per_route=1, min_per_query_type=1, min_per_grade=1, max_total=100)
        sampler = StratifiedSampler(config)
        result = sampler.stratify_pairs(pairs)
        assert len(result) == 3

    def test_stratify_respects_max_total(self):
        """Total capped at max_total."""
        pairs = [
            {"id": f"p{i}", "tier": 1, "route": "sql", "query_type": "lookup", "quality_grade": "gold", "query": f"query {i}"}
            for i in range(200)
        ]
        config = SamplingConfig(min_tier1=1, min_per_route=1, min_per_query_type=1, min_per_grade=1, max_total=50)
        sampler = StratifiedSampler(config)
        result = sampler.stratify_pairs(pairs)
        assert len(result) <= 50

    def test_no_query_type_zero_buckets(self):
        """All 6 query types represented if available."""
        pairs = [
            {"id": f"p{i}", "tier": 1, "route": "sql", "query_type": qt, "quality_grade": "gold", "query": "test"}
            for i, qt in enumerate(["lookup", "aggregation", "comparison", "time_series", "top_n", "cross_domain"])
            for _ in range(50)
        ]
        config = SamplingConfig(min_tier1=1, min_per_route=1, min_per_query_type=10, min_per_grade=1, max_total=10000)
        sampler = StratifiedSampler(config)
        result = sampler.stratify_pairs(pairs)
        profile = sampler.compute_diversity_profile(result)
        assert all(qt in profile["query_type"] for qt in ["lookup", "aggregation", "comparison", "time_series", "top_n", "cross_domain"])

    def test_empty_input_returns_empty(self):
        """No pairs returns empty list."""
        config = SamplingConfig()
        sampler = StratifiedSampler(config)
        result = sampler.stratify_pairs([])
        assert result == []

    def test_oversample_flag_upsamples_minority(self):
        """With oversample=True, minority large buckets get upsampled."""
        pairs = [
            {"id": "gold1", "tier": 1, "route": "sql", "query_type": "lookup", "quality_grade": "gold", "query": "find researchers"},
            {"id": "gold2", "tier": 2, "route": "sql", "query_type": "lookup", "quality_grade": "gold", "query": "list labs"},
            {"id": "silver1", "tier": 1, "route": "sql", "query_type": "lookup", "quality_grade": "silver", "query": "test"},
        ]
        config = SamplingConfig(
            min_tier1=1,
            min_per_route=1,
            min_per_query_type=1,
            min_per_grade=1,
            max_total=100,
            oversample_if_needed=True,
        )
        sampler = StratifiedSampler(config)
        result = sampler.stratify_pairs(pairs)
        result_ids = [p["id"] for p in result]
        assert "gold1" in result_ids
        assert "gold2" in result_ids


class TestDiversityProfile:
    """Tests for compute_diversity_profile method."""

    def test_diversity_profile_computed(self):
        """Returns correct breakdown."""
        pairs = [
            {"id": "p1", "tier": 1, "route": "sql", "query_type": "lookup", "quality_grade": "gold", "query": "find researchers"},
            {"id": "p2", "tier": 1, "route": "sql", "query_type": "lookup", "quality_grade": "gold", "query": "list labs"},
            {"id": "p3", "tier": 2, "route": "rag", "query_type": "aggregation", "quality_grade": "silver", "query": "count publications"},
            {"id": "p4", "tier": 3, "route": "hybrid", "query_type": "comparison", "quality_grade": "bronze", "query": "compare labs"},
        ]
        config = SamplingConfig()
        sampler = StratifiedSampler(config)
        profile = sampler.compute_diversity_profile(pairs)
        assert profile["tier"]["tier1"] == 2
        assert profile["tier"]["tier2"] == 1
        assert profile["tier"]["tier3"] == 1
        assert profile["route"]["sql"] == 2
        assert profile["route"]["rag"] == 1
        assert profile["route"]["hybrid"] == 1
        assert profile["query_type"]["lookup"] == 2
        assert profile["query_type"]["aggregation"] == 1
        assert profile["query_type"]["comparison"] == 1
        assert profile["grade"]["gold"] == 2
        assert profile["grade"]["silver"] == 1
        assert profile["grade"]["bronze"] == 1


class TestGoldPreservation:
    """Tests for gold pair preservation."""

    def test_balanced_sample_preserves_gold_pairs(self):
        """Gold pairs always included."""
        pairs = [
            {"id": "gold1", "tier": 1, "route": "sql", "query_type": "lookup", "quality_grade": "gold", "query": "find researchers"},
            {"id": "gold2", "tier": 2, "route": "sql", "query_type": "lookup", "quality_grade": "gold", "query": "list labs"},
        ] + [
            {"id": f"p{i}", "tier": 1, "route": "sql", "query_type": "lookup", "quality_grade": "bronze", "query": f"query {i}"}
            for i in range(100)
        ]
        config = SamplingConfig(
            min_tier1=1,
            min_per_route=1,
            min_per_query_type=1,
            min_per_grade=1,
            max_total=50,
        )
        sampler = StratifiedSampler(config)
        result = sampler.stratify_pairs(pairs)
        result_ids = [p["id"] for p in result]
        assert "gold1" in result_ids
        assert "gold2" in result_ids


class TestIntegration:
    """Integration tests."""

    def test_get_balanced_sample_main_entry_point(self):
        """get_balanced_sample is the main entry point."""
        pairs = [
            {"id": "p1", "tier": 1, "route": "sql", "query_type": "lookup", "quality_grade": "gold", "query": "find researchers"},
        ]
        config = SamplingConfig(max_total=10)
        result = get_balanced_sample(pairs, config)
        assert len(result) >= 1

    def test_default_config_values(self):
        """Default config has correct values."""
        config = SamplingConfig()
        assert config.min_tier1 == 50
        assert config.min_tier2 == 30
        assert config.min_tier3 == 20
        assert config.min_per_route == 20
        assert config.min_per_query_type == 10
        assert config.min_per_grade == 10
        assert config.max_total == 10000
        assert config.oversample_if_needed is False
