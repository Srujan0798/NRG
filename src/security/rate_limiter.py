"""Redis-based tiered rate limiting with X-RateLimit headers.

Rate Limits Per Tier:
- Researcher: 100 requests/minute
- Government: 200 requests/minute
- Industry: 50 requests/minute

Per-Endpoint Rate Limits:
- /query: 10 requests/minute per user
- /login: 5 requests/minute per IP
- /health: 60 requests/minute per IP
"""

import logging
import os
import time
from typing import Optional

from src.caching.redis_layer import _get_redis

logger = logging.getLogger(__name__)

TIER_LIMITS = {
    1: 100,
    2: 200,
    3: 50,
}

TIER_NAMES = {
    1: "researcher",
    2: "government",
    3: "industry",
}

ENDPOINT_LIMITS = {
    "/query": 10,
    "/login": 5,
    "/health": 60,
}

REQUESTS_PER_MINUTE = 60


def _is_test_mode() -> bool:
    """Check if we're running in test mode."""
    quota_disabled = os.environ.get("NRG_QUOTA_DISABLED", "").lower()
    return (
        os.environ.get("PYTEST_CURRENT_TEST") is not None
        or os.environ.get("TESTING") == "true"
        or quota_disabled in {"1", "true", "yes"}
    )


class TieredRateLimiter:
    """Redis-backed distributed rate limiter with tier-based limits."""

    def __init__(self):
        self._redis = None
        self._tier_limits = TIER_LIMITS.copy()
        self._window_seconds = REQUESTS_PER_MINUTE

    def _get_redis_client(self):
        if self._redis is None:
            self._redis = _get_redis()
        return self._redis

    def _make_key(self, identifier: str, tier: int) -> str:
        return f"ratelimit:{TIER_NAMES.get(tier, 'researcher')}:{identifier}"

    def check_rate_limit(
        self,
        identifier: str,
        tier: int,
        ip: Optional[str] = None,
    ) -> tuple[bool, int, int]:
        """Check if request is within rate limit.

        Returns:
            (allowed: bool, remaining: int, reset_time: int)
        """
        if _is_test_mode():
            limit = self._tier_limits.get(tier, 100)
            return True, limit, 0

        client = self._get_redis_client()
        key = self._make_key(identifier, tier)
        limit = self._tier_limits.get(tier, 100)

        if client is None:
            return True, limit, 0

        now = time.time()
        window_start = now - self._window_seconds

        pipe = client.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        pipe.zadd(key, {str(now): now})
        pipe.expire(key, self._window_seconds + 1)
        results = pipe.execute()

        current_count = results[1]
        remaining = max(0, limit - current_count - 1)
        reset_time = int(now + self._window_seconds)

        if current_count >= limit:
            return False, 0, reset_time

        return True, remaining, reset_time

    def get_rate_limit_headers(
        self,
        tier: int,
        allowed: bool,
        remaining: int,
        reset_time: int,
    ) -> dict[str, str]:
        """Generate X-RateLimit response headers."""
        limit = self._tier_limits.get(tier, 100)
        return {
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_time),
            "X-RateLimit-Window": str(self._window_seconds),
            "X-RateLimit-Tier": TIER_NAMES.get(tier, "unknown"),
        }

    def set_tier_limit(self, tier: int, limit: int) -> None:
        self._tier_limits[tier] = limit

    def get_usage_stats(self, identifier: str, tier: int) -> dict:
        """Get current usage stats for an identifier."""
        client = self._get_redis_client()
        key = self._make_key(identifier, tier)

        if client is None:
            return {"available": False}

        now = time.time()
        window_start = now - self._window_seconds

        client.zremrangebyscore(key, 0, window_start)
        count = client.zcard(key)
        limit = self._tier_limits.get(tier, 100)

        return {
            "available": True,
            "current_usage": count,
            "limit": limit,
            "remaining": max(0, limit - count),
            "window_seconds": self._window_seconds,
        }


_rate_limiter_instance: Optional[TieredRateLimiter] = None


def get_rate_limiter() -> TieredRateLimiter:
    global _rate_limiter_instance
    if _rate_limiter_instance is None:
        _rate_limiter_instance = TieredRateLimiter()
    return _rate_limiter_instance


def check_tier_rate_limit(
    user_id: str,
    tier: int,
    ip: Optional[str] = None,
) -> tuple[bool, int, int, dict]:
    """Convenience function to check rate limit and get headers.

    Returns:
        (allowed, remaining, reset_time, headers)
    """
    limiter = get_rate_limiter()
    identifier = ip if ip else user_id
    allowed, remaining, reset_time = limiter.check_rate_limit(identifier, tier, ip)
    headers = limiter.get_rate_limit_headers(tier, allowed, remaining, reset_time)
    return allowed, remaining, reset_time, headers


class EndpointRateLimiter:
    """Redis-backed per-endpoint rate limiter for sensitive endpoints."""

    def __init__(self):
        self._redis = None
        self._endpoint_limits = ENDPOINT_LIMITS.copy()
        self._window_seconds = 60

    def _get_redis_client(self):
        if self._redis is None:
            self._redis = _get_redis()
        return self._redis

    def _make_key(self, endpoint: str, identifier: str) -> str:
        safe_endpoint = endpoint.replace("/", "_")
        return f"endpoint_ratelimit:{safe_endpoint}:{identifier}"

    def check_endpoint_limit(
        self,
        endpoint: str,
        identifier: str,
    ) -> tuple[bool, int, int]:
        """Check if request to endpoint is within rate limit.

        Returns:
            (allowed: bool, remaining: int, reset_time: int)
        """
        if _is_test_mode():
            limit = self._endpoint_limits.get(endpoint, 60)
            return True, limit, 0

        client = self._get_redis_client()
        key = self._make_key(endpoint, identifier)
        limit = self._endpoint_limits.get(endpoint, 60)

        if client is None:
            return True, limit, 0

        now = time.time()
        window_start = now - self._window_seconds

        pipe = client.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        pipe.zadd(key, {str(now): now})
        pipe.expire(key, self._window_seconds + 1)
        results = pipe.execute()

        current_count = results[1]
        remaining = max(0, limit - current_count - 1)
        reset_time = int(now + self._window_seconds)

        if current_count >= limit:
            logger.warning(
                "Endpoint rate limit exceeded: %s for %s (count=%d, limit=%d)",
                endpoint,
                identifier,
                current_count,
                limit,
            )
            return False, 0, reset_time

        return True, remaining, reset_time

    def get_endpoint_headers(
        self,
        endpoint: str,
        allowed: bool,
        remaining: int,
        reset_time: int,
    ) -> dict[str, str]:
        """Generate X-RateLimit response headers for endpoint."""
        limit = self._endpoint_limits.get(endpoint, 60)
        return {
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_time),
            "X-RateLimit-Window": str(self._window_seconds),
            "X-RateLimit-Policy": f"endpoint-{endpoint}",
        }

    def set_endpoint_limit(self, endpoint: str, limit: int) -> None:
        """Override rate limit for an endpoint."""
        self._endpoint_limits[endpoint] = limit


_endpoint_limiter_instance: Optional[EndpointRateLimiter] = None


def get_endpoint_limiter() -> EndpointRateLimiter:
    global _endpoint_limiter_instance
    if _endpoint_limiter_instance is None:
        _endpoint_limiter_instance = EndpointRateLimiter()
    return _endpoint_limiter_instance


def check_endpoint_rate_limit(
    endpoint: str,
    identifier: str,
) -> tuple[bool, int, int, dict]:
    """Check endpoint-specific rate limit.

    Returns:
        (allowed, remaining, reset_time, headers)
    """
    limiter = get_endpoint_limiter()
    allowed, remaining, reset_time = limiter.check_endpoint_limit(endpoint, identifier)
    headers = limiter.get_endpoint_headers(endpoint, allowed, remaining, reset_time)
    return allowed, remaining, reset_time, headers
