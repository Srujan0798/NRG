"""Tests for CostGuard LLM Budget Governance."""

from unittest.mock import patch


class TestCostGuardBudgetStatus:
    """Test budget status reporting."""

    def test_get_budget_status_healthy(self):
        from src.config.llm_config import CostGuard

        CostGuard.reset_instance()
        with patch.object(CostGuard, "_load_from_storage", return_value=None):
            with patch.object(CostGuard, "_load_spent_from_redis", return_value=None):
                cg = CostGuard.__new__(CostGuard)
                cg.monthly_budget_inr = 500000.0
                cg._spent_this_month = 100000.0
                cg._month_start = 0
                cg._query_count = 10
                cg._allocation_lock = __import__("threading").Lock()
                cg._allocate_budget()

                status = cg.get_budget_status()
                assert status["spent_inr"] == 100000.0
                assert status["budget_inr"] == 500000.0
                assert status["percentage"] == 0.2
                assert status["percentage_display"] == "20.0%"
                assert status["warning"] is False
                assert status["critical"] is False
                assert status["halt"] is False

    def test_get_budget_status_warning(self):
        from src.config.llm_config import CostGuard

        CostGuard.reset_instance()
        with patch.object(CostGuard, "_load_from_storage", return_value=None):
            with patch.object(CostGuard, "_load_spent_from_redis", return_value=None):
                cg = CostGuard.__new__(CostGuard)
                cg.monthly_budget_inr = 500000.0
                cg._spent_this_month = 380000.0
                cg._month_start = 0
                cg._query_count = 500
                cg._allocation_lock = __import__("threading").Lock()
                cg._allocate_budget()

                status = cg.get_budget_status()
                assert status["warning"] is True
                assert status["critical"] is False
                assert status["halt"] is False

    def test_get_budget_status_critical(self):
        from src.config.llm_config import CostGuard

        CostGuard.reset_instance()
        with patch.object(CostGuard, "_load_from_storage", return_value=None):
            with patch.object(CostGuard, "_load_spent_from_redis", return_value=None):
                cg = CostGuard.__new__(CostGuard)
                cg.monthly_budget_inr = 500000.0
                cg._spent_this_month = 450000.0
                cg._month_start = 0
                cg._query_count = 2000
                cg._allocation_lock = __import__("threading").Lock()
                cg._allocate_budget()

                status = cg.get_budget_status()
                assert status["warning"] is True
                assert status["critical"] is True
                assert status["halt"] is False

    def test_get_budget_status_halt(self):
        from src.config.llm_config import CostGuard

        CostGuard.reset_instance()
        with patch.object(CostGuard, "_load_from_storage", return_value=None):
            with patch.object(CostGuard, "_load_spent_from_redis", return_value=None):
                cg = CostGuard.__new__(CostGuard)
                cg.monthly_budget_inr = 500000.0
                cg._spent_this_month = 480000.0
                cg._month_start = 0
                cg._query_count = 5000
                cg._allocation_lock = __import__("threading").Lock()
                cg._allocate_budget()

                status = cg.get_budget_status()
                assert status["warning"] is True
                assert status["critical"] is True
                assert status["halt"] is True


class TestCostGuardCheckBudget:
    """Test budget enforcement logic."""

    def _make_cg(self, spent_pct: float = 0.0):
        from src.config.llm_config import CostGuard
        import threading

        CostGuard.reset_instance()
        with patch.object(CostGuard, "_load_from_storage", return_value=None):
            with patch.object(CostGuard, "_load_spent_from_redis", return_value=None):
                cg = CostGuard.__new__(CostGuard)
                cg.monthly_budget_inr = 500000.0
                cg._spent_this_month = 500000.0 * spent_pct
                cg._month_start = 0
                cg._query_count = 0
                cg._allocation_lock = threading.Lock()
                cg._allocate_budget()
                return cg

    def test_researcher_trivial_allowed(self):
        cg = self._make_cg(0.0)
        allowed, reason = cg.check_budget(user_tier=1, complexity="trivial", estimated_cost=0.0)
        assert allowed is True
        assert reason == ""

    def test_researcher_simple_allowed_under_cap(self):
        cg = self._make_cg(0.0)
        allowed, reason = cg.check_budget(user_tier=1, complexity="simple", estimated_cost=3.0)
        assert allowed is True
        assert reason == ""

    def test_researcher_simple_blocked_over_cap(self):
        cg = self._make_cg(0.0)
        allowed, reason = cg.check_budget(user_tier=1, complexity="simple", estimated_cost=10.0)
        assert allowed is False
        assert "exceeds simple cap" in reason

    def test_researcher_complex_blocked_over_cap(self):
        cg = self._make_cg(0.0)
        allowed, reason = cg.check_budget(user_tier=1, complexity="complex", estimated_cost=500.0)
        assert allowed is False
        assert "exceeds complex cap" in reason

    def test_researcher_complex_allowed_with_guru_approval(self):
        cg = self._make_cg(0.0)
        allowed, reason = cg.check_budget(
            user_tier=1, complexity="complex", estimated_cost=500.0, guru_approval="ABC-123"
        )
        assert allowed is True
        assert "guru_approved" in reason

    def test_government_tier_sovereign_override(self):
        cg = self._make_cg(0.0)
        allowed, reason = cg.check_budget(user_tier=2, complexity="complex", estimated_cost=999.0)
        assert allowed is True
        assert reason == "government_tier_sovereign_override"

    def test_government_tier_not_blocked_at_halt(self):
        cg = self._make_cg(0.96)
        allowed, reason = cg.check_budget(user_tier=2, complexity="complex", estimated_cost=999.0)
        assert allowed is True
        assert reason == "government_tier_sovereign_override"

    def test_industry_tier_capped(self):
        cg = self._make_cg(0.0)
        allowed, reason = cg.check_budget(user_tier=3, complexity="simple", estimated_cost=3.0)
        assert allowed is True

        allowed2, reason2 = cg.check_budget(user_tier=3, complexity="simple", estimated_cost=10.0)
        assert allowed2 is False
        assert "Industry tier capped at" in reason2

    def test_industry_tier_trivial_allowed(self):
        cg = self._make_cg(0.0)
        allowed, reason = cg.check_budget(user_tier=3, complexity="trivial", estimated_cost=0.0)
        assert allowed is True

    def test_halt_blocks_cloud_llms_without_override(self):
        cg = self._make_cg(0.96)
        cg._spent_by_tier["incident_reserve"] = cg._budget_by_tier["incident_reserve"]
        allowed, reason = cg.check_budget(user_tier=1, complexity="standard", estimated_cost=10.0)
        assert allowed is False
        assert "95%" in reason or "disabled" in reason

    def test_halt_allows_with_guru_override(self):
        cg = self._make_cg(0.96)
        allowed, reason = cg.check_budget(
            user_tier=1, complexity="standard", estimated_cost=10.0, guru_approval="XYZ-999"
        )
        assert allowed is True
        assert "guru_override" in reason

    def test_halt_allows_incident_reserve_not_exhausted(self):
        cg = self._make_cg(0.96)
        cg._spent_by_tier["incident_reserve"] = cg._budget_by_tier["incident_reserve"] - 1
        allowed, reason = cg.check_budget(user_tier=1, complexity="standard", estimated_cost=10.0)
        assert allowed is True
        assert "incident_reserve_override" in reason

    def test_critical_blocks_simple_without_approval(self):
        cg = self._make_cg(0.88)
        allowed, reason = cg.check_budget(user_tier=1, complexity="simple", estimated_cost=3.0)
        assert allowed is False
        assert "critical" in reason or "blocked" in reason

    def test_critical_allows_trivial(self):
        cg = self._make_cg(0.88)
        allowed, reason = cg.check_budget(user_tier=1, complexity="trivial", estimated_cost=0.0)
        assert allowed is True


class TestCostGuardGetProviderForTier:
    """Test provider routing by persona."""

    def _make_cg(self):
        from src.config.llm_config import CostGuard
        import threading

        CostGuard.reset_instance()
        with patch.object(CostGuard, "_load_from_storage", return_value=None):
            with patch.object(CostGuard, "_load_spent_from_redis", return_value=None):
                cg = CostGuard.__new__(CostGuard)
                cg.monthly_budget_inr = 500000.0
                cg._spent_this_month = 0.0
                cg._month_start = 0
                cg._query_count = 0
                cg._allocation_lock = threading.Lock()
                cg._allocate_budget()
                return cg

    def test_government_tier_gets_minimax_first(self):
        cg = self._make_cg()
        providers = cg.get_provider_for_tier(user_tier=2, complexity="complex")
        assert providers[0] == "minimax"
        assert "nvidia" in providers

    def test_industry_tier_gets_local_first(self):
        cg = self._make_cg()
        providers = cg.get_provider_for_tier(user_tier=3, complexity="simple")
        assert providers[0] == "local"

    def test_researcher_trivial_gets_rule_based(self):
        cg = self._make_cg()
        providers = cg.get_provider_for_tier(user_tier=1, complexity="trivial")
        assert providers[0] == "rule_based"

    def test_researcher_complex_gets_cloud_providers(self):
        cg = self._make_cg()
        providers = cg.get_provider_for_tier(user_tier=1, complexity="complex")
        assert providers[0] == "azure"


class TestCostGuardEstimateCost:
    """Test cost estimation."""

    def _make_cg(self):
        from src.config.llm_config import CostGuard
        import threading

        CostGuard.reset_instance()
        with patch.object(CostGuard, "_load_from_storage", return_value=None):
            with patch.object(CostGuard, "_load_spent_from_redis", return_value=None):
                cg = CostGuard.__new__(CostGuard)
                cg.monthly_budget_inr = 500000.0
                cg._spent_this_month = 0.0
                cg._month_start = 0
                cg._query_count = 0
                cg._allocation_lock = threading.Lock()
                cg._allocate_budget()
                return cg

    def test_local_is_free(self):
        cg = self._make_cg()
        cost = cg.estimate_cost(complexity="simple", provider="local", tokens_in=1000, tokens_out=200)
        assert cost == 0.0

    def test_rule_based_is_free(self):
        cg = self._make_cg()
        cost = cg.estimate_cost(complexity="trivial", provider="rule_based", tokens_in=100, tokens_out=50)
        assert cost == 0.0

    def test_minimax_estimated(self):
        cg = self._make_cg()
        cost = cg.estimate_cost(complexity="moderate", provider="minimax", tokens_in=1000, tokens_out=200)
        assert cost > 0

    def test_cost_capped_at_complexity_max(self):
        cg = self._make_cg()
        cost = cg.estimate_cost(complexity="complex", provider="openai", tokens_in=60000, tokens_out=15000)
        assert cost == 200.0


class TestCostGuardGetDailyCostDigest:
    """Test daily digest string."""

    def _make_cg(self, spent_pct: float = 0.0):
        from src.config.llm_config import CostGuard
        import threading

        CostGuard.reset_instance()
        with patch.object(CostGuard, "_load_from_storage", return_value=None):
            with patch.object(CostGuard, "_load_spent_from_redis", return_value=None):
                cg = CostGuard.__new__(CostGuard)
                cg.monthly_budget_inr = 500000.0
                cg._spent_this_month = 500000.0 * spent_pct
                cg._month_start = 0
                cg._query_count = 100
                cg._allocation_lock = threading.Lock()
                cg._allocate_budget()
                return cg

    def test_digest_no_alerts(self):
        cg = self._make_cg(0.3)
        digest = cg.get_daily_cost_digest()
        assert "COST:" in digest
        assert "No alerts" in digest

    def test_digest_warning(self):
        cg = self._make_cg(0.72)
        digest = cg.get_daily_cost_digest()
        assert "WARNING" in digest

    def test_digest_critical(self):
        cg = self._make_cg(0.88)
        digest = cg.get_daily_cost_digest()
        assert "CRITICAL" in digest

    def test_digest_halt(self):
        cg = self._make_cg(0.96)
        digest = cg.get_daily_cost_digest()
        assert "HALT" in digest


class TestCostGuardRecordCost:
    """Test cost recording updates counters."""

    def _make_cg(self):
        from src.config.llm_config import CostGuard
        import threading

        CostGuard.reset_instance()
        with patch.object(CostGuard, "_load_from_storage", return_value=None):
            with patch.object(CostGuard, "_load_spent_from_redis", return_value=None):
                cg = CostGuard.__new__(CostGuard)
                cg.monthly_budget_inr = 500000.0
                cg._spent_this_month = 10000.0
                cg._month_start = 0
                cg._query_count = 5
                cg._allocation_lock = threading.Lock()
                cg._redis = None
                cg._redis_key_prefix = "costguard:monthly:"
                cg._allocate_budget()
                return cg

    def test_record_cost_updates_spent(self):
        from src.config.llm_config import CostGuard

        CostGuard.reset_instance()
        cg = self._make_cg()
        initial_spent = cg._spent_this_month

        with patch("src.audit.log_cost_decision") as mock_log:
            mock_log.return_value = "abc123"
            cg.record_cost(
                query_id="test-001",
                provider="minimax",
                tokens_in=1000,
                tokens_out=200,
                cost_inr=5.0,
                persona="researcher",
                complexity="moderate",
                route_decision="cloud_llm",
            )

        assert cg._spent_this_month == initial_spent + 5.0
        assert cg._query_count == 6

    def test_record_cost_updates_tier_spent(self):
        from src.config.llm_config import CostGuard

        CostGuard.reset_instance()
        cg = self._make_cg()

        with patch("src.audit.log_cost_decision") as mock_log:
            mock_log.return_value = "abc123"
            cg.record_cost(
                query_id="test-002",
                provider="minimax",
                tokens_in=1000,
                tokens_out=200,
                cost_inr=10.0,
                persona="government",
                complexity="complex",
                route_decision="cloud_llm",
            )

        assert cg._spent_by_tier["government_tier"] == 10.0


class TestCostGuardEstimateTokens:
    """Test token estimation."""

    def _make_cg(self):
        from src.config.llm_config import CostGuard
        import threading

        CostGuard.reset_instance()
        with patch.object(CostGuard, "_load_from_storage", return_value=None):
            with patch.object(CostGuard, "_load_spent_from_redis", return_value=None):
                cg = CostGuard.__new__(CostGuard)
                cg.monthly_budget_inr = 500000.0
                cg._spent_this_month = 0.0
                cg._month_start = 0
                cg._query_count = 0
                cg._allocation_lock = threading.Lock()
                cg._allocate_budget()
                return cg

    def test_estimate_tokens_basic(self):
        cg = self._make_cg()
        tokens_in, tokens_out = cg.estimate_tokens("list researchers in Gujarat", context_chunks=5)
        assert tokens_in > 0
        assert tokens_out > 0

    def test_estimate_tokens_scales_with_context(self):
        cg = self._make_cg()
        _, out_0 = cg.estimate_tokens("test query", context_chunks=0)
        _, out_5 = cg.estimate_tokens("test query", context_chunks=5)
        assert out_5 > out_0

    def test_estimate_tokens_from_explicit_counts(self):
        cg = self._make_cg()
        cost = cg.estimate_cost(
            complexity="standard",
            provider="minimax",
            tokens_in=2000,
            tokens_out=500,
        )
        assert cost > 0


class TestCostGuardTierMapping:
    """Test user tier to tier key mapping."""

    def _make_cg(self):
        from src.config.llm_config import CostGuard
        import threading

        CostGuard.reset_instance()
        with patch.object(CostGuard, "_load_from_storage", return_value=None):
            with patch.object(CostGuard, "_load_spent_from_redis", return_value=None):
                cg = CostGuard.__new__(CostGuard)
                cg.monthly_budget_inr = 500000.0
                cg._spent_this_month = 0.0
                cg._month_start = 0
                cg._query_count = 0
                cg._allocation_lock = threading.Lock()
                cg._allocate_budget()
                return cg

    def test_tier_1_maps_to_researcher(self):
        cg = self._make_cg()
        assert cg.get_tier_key(1) == "researcher_tier"

    def test_tier_2_maps_to_government(self):
        cg = self._make_cg()
        assert cg.get_tier_key(2) == "government_tier"

    def test_tier_3_maps_to_industry(self):
        cg = self._make_cg()
        assert cg.get_tier_key(3) == "industry_tier"

    def test_unknown_tier_defaults_to_researcher(self):
        cg = self._make_cg()
        assert cg.get_tier_key(99) == "researcher_tier"


class TestCostGuardAllocation:
    """Test budget allocation by tier."""

    def _make_cg(self):
        from src.config.llm_config import CostGuard
        import threading

        CostGuard.reset_instance()
        with patch.object(CostGuard, "_load_from_storage", return_value=None):
            with patch.object(CostGuard, "_load_spent_from_redis", return_value=None):
                cg = CostGuard.__new__(CostGuard)
                cg.monthly_budget_inr = 500000.0
                cg._spent_this_month = 0.0
                cg._month_start = 0
                cg._query_count = 0
                cg._allocation_lock = threading.Lock()
                cg._allocate_budget()
                return cg

    def test_allocation_sums_to_total(self):
        cg = self._make_cg()
        total = sum(cg._budget_by_tier.values())
        assert total == 500000.0

    def test_researcher_gets_40_percent(self):
        cg = self._make_cg()
        assert cg._budget_by_tier["researcher_tier"] == 200000.0

    def test_government_gets_35_percent(self):
        cg = self._make_cg()
        assert cg._budget_by_tier["government_tier"] == 175000.0

    def test_industry_gets_15_percent(self):
        cg = self._make_cg()
        assert cg._budget_by_tier["industry_tier"] == 75000.0

    def test_spent_by_tier_starts_at_zero(self):
        cg = self._make_cg()
        assert all(v == 0.0 for v in cg._spent_by_tier.values())
