import json
import logging
from functools import wraps
from redis import Redis

logger = logging.getLogger(__name__)

# Default Redis connection
redis_cache = Redis(host='localhost', port=6379, db=0, decode_responses=True)

def cache_query(ttl=300):
    """Decorator to cache results of LangGraph workflow runs."""
    def decorator(func):
        @wraps(func)
        def wrapper(self, query, user_tier=1, *args, **kwargs):
            # Create a deterministic cache key
            # session_id should probably NOT be part of the cache key for global reuse, 
            # or it should be handled based on user requirements.
            # Here we follow the protocol's guidance.
            cache_key = f"query:{hash(query)}:{user_tier}"
            
            try:
                cached = redis_cache.get(cache_key)
                if cached:
                    logger.info(f"Cache HIT for key: {cache_key}")
                    return json.loads(cached)
            except Exception as e:
                logger.warning(f"Cache lookup failed: {e}")
            
            # Call original function
            result = func(self, query, user_tier, *args, **kwargs)
            
            try:
                # Store result in cache
                # We need a custom serializer for non-serializable objects (like some UUIDs)
                # But here we just use default=str for safety.
                redis_cache.setex(cache_key, ttl, json.dumps(result, default=str))
                logger.info(f"Cache MISS, stored key: {cache_key}")
            except Exception as e:
                logger.warning(f"Cache storage failed: {e}")
                
            return result
        return wrapper
    return decorator
