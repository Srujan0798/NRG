"""Rate limiting middleware with tier-based quotas."""

import time
import redis

from fastapi import HTTPException, Request


class QuotaManager:
    """Token-bucket rate limiter with Redis backend."""
    
    # Tier limits: (requests_per_minute, requests_per_day)
    TIER_LIMITS = {
        1: (100, 10000),  # Researcher
        2: (50, 5000),    # Government
        3: (20, 2000),    # Industry
    }
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis = redis.from_url(redis_url)
        self.bucket_size = 60  # seconds
    
    def _get_key(self, user_id: str, tier: int, window: str) -> str:
        """Generate Redis key for rate limit."""
        return f"quota:{user_id}:tier{tier}:{window}"
    
    def check_quota(self, user_id: str, tier: int) -> dict:
        """Check if user has quota available."""
        minute_limit, day_limit = self.TIER_LIMITS.get(tier, (10, 1000))
        
        now = int(time.time())
        minute_key = self._get_key(user_id, tier, f"minute:{now // 60}")
        day_key = self._get_key(user_id, tier, f"day:{now // 86400}")
        
        # Increment counters
        pipe = self.redis.pipeline()
        pipe.incr(minute_key)
        pipe.expire(minute_key, 120)  # 2 min expiry
        pipe.incr(day_key)
        pipe.expire(day_key, 172800)  # 2 day expiry
        results = pipe.execute()
        
        minute_count = results[0]
        day_count = results[2]
        
        allowed = minute_count <= minute_limit and day_count <= day_limit
        
        return {
            "allowed": allowed,
            "tier": tier,
            "minute_used": minute_count,
            "minute_limit": minute_limit,
            "day_used": day_count,
            "day_limit": day_limit,
            "remaining": min(minute_limit - minute_count, day_limit - day_count),
            "reset_at": (now // 60 + 1) * 60,
        }
    
    def enforce_quota(self, user_id: str, tier: int):
        """Enforce quota or raise exception."""
        result = self.check_quota(user_id, tier)
        
        if not result["allowed"]:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "quota": result,
                },
                headers={
                    "X-RateLimit-Limit": str(result["minute_limit"]),
                    "X-RateLimit-Remaining": str(max(0, result["remaining"])),
                    "X-RateLimit-Reset": str(result["reset_at"]),
                }
            )
        
        return result


quota_manager = QuotaManager()


def rate_limit_tiered(request: Request):
    """Dependency for rate limiting by tier."""
    user_id = request.state.user.get("sub", "anonymous")
    tier = request.state.user.get("tier", 1)
    return quota_manager.enforce_quota(user_id, tier)
