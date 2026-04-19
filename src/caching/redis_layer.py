import json
import logging
from functools import wraps

logger = logging.getLogger(__name__)

_redis_client = None
_redis_checked = False
_redis_warned = False
REDIS_AVAILABLE: bool = False


def _warn_once(msg: str, *args):
    global _redis_warned
    if not _redis_warned:
        _redis_warned = True
        logger.warning(msg, *args)


def _get_redis():
    """Return a working Redis client, or None.

    Connection is created lazily on first call and reused.
    If Redis is unreachable at startup or at runtime, returns None
    and the caller falls through without caching.
    """
    global _redis_client, _redis_checked

    if _redis_checked:
        return _redis_client

    _redis_checked = True
    try:
        from redis import Redis

        client = Redis(
            host="localhost",
            port=6379,
            db=0,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        client.ping()
        _redis_client = client
        global REDIS_AVAILABLE
        REDIS_AVAILABLE = True
        logger.info("Redis cache is available")
    except Exception:
        _redis_client = None
        _warn_once("Redis cache is not available - running without caching")

    return _redis_client


def _mark_redis_unavailable():
    global _redis_client, REDIS_AVAILABLE
    _redis_client = None
    REDIS_AVAILABLE = False


def cache_query(ttl=300):
    """Decorator to cache results of LangGraph workflow runs.

    Gracefully degrades: if Redis is unreachable (at import, startup,
    or runtime) the wrapped function executes normally without caching.
    Never raises due to Redis unavailability. Logs a single warning.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                client = _get_redis()

                if client is None:
                    return func(*args, **kwargs)

                query = args[1] if len(args) > 1 else kwargs.get("query", "")
                user_tier = args[2] if len(args) > 2 else kwargs.get("user_tier", 1)
                cache_key = f"query:{hash(query)}:{user_tier}"

                try:
                    cached = client.get(cache_key)
                    if cached:
                        logger.info("Cache HIT for key: %s", cache_key)
                        return json.loads(cached)
                except Exception as e:
                    _warn_once("Redis cache failed, disabling caching: %s", e)
                    _mark_redis_unavailable()
                    return func(*args, **kwargs)

                result = func(*args, **kwargs)

                try:
                    client.setex(cache_key, ttl, json.dumps(result, default=str))
                    logger.info("Cache MISS, stored key: %s", cache_key)
                except Exception as e:
                    _warn_once("Redis cache failed, disabling caching: %s", e)
                    _mark_redis_unavailable()

                return result
            except Exception:
                return func(*args, **kwargs)
        return wrapper
    return decorator
