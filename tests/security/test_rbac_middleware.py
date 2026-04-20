"""Tests for RBAC middleware."""


from src.security.rbac.middleware import RBACMiddleware


class TestRBACMiddleware:
    def test_default_tier(self):
        middleware = RBACMiddleware()
        assert middleware.user_tier == 3

    def test_custom_tier(self):
        middleware = RBACMiddleware(user_tier=1)
        assert middleware.user_tier == 1

    def test_get_allowed_tiers_researcher(self):
        middleware = RBACMiddleware()
        assert middleware.get_allowed_tiers("researcher") == [1, 2, 3]

    def test_get_allowed_tiers_government(self):
        middleware = RBACMiddleware()
        assert middleware.get_allowed_tiers("government") == [2, 3]

    def test_get_allowed_tiers_industry(self):
        middleware = RBACMiddleware()
        assert middleware.get_allowed_tiers("industry") == [3]

    def test_get_allowed_tiers_unknown(self):
        middleware = RBACMiddleware()
        assert middleware.get_allowed_tiers("unknown") == [3]

    def test_inject_postgresql_filter(self):
        middleware = RBACMiddleware(user_tier=2)
        query, params = middleware.inject_postgresql_filter("SELECT * FROM researchers")
        assert "SELECT" in query

    def test_inject_qdrant_filter(self):
        middleware = RBACMiddleware(user_tier=1)
        query = {"vector": [0.1, 0.2]}
        result = middleware.inject_qdrant_filter(query)
        assert "vector" in result

    def test_validate_tier_access_tier1(self):
        middleware = RBACMiddleware(user_tier=1)
        assert middleware.validate_tier_access(1) is True
        assert middleware.validate_tier_access(2) is True
        assert middleware.validate_tier_access(3) is True

    def test_validate_tier_access_tier2(self):
        middleware = RBACMiddleware(user_tier=2)
        assert middleware.validate_tier_access(1) is False
        assert middleware.validate_tier_access(2) is True
        assert middleware.validate_tier_access(3) is True

    def test_validate_tier_access_tier3(self):
        middleware = RBACMiddleware(user_tier=3)
        assert middleware.validate_tier_access(1) is False
        assert middleware.validate_tier_access(2) is False
        assert middleware.validate_tier_access(3) is True

    def test_validate_tier_access_invalid(self):
        middleware = RBACMiddleware(user_tier=99)
        assert middleware.validate_tier_access(1) is False
