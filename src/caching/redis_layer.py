import json
import logging
import os
from functools import wraps
from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar, cast

logger = logging.getLogger(__name__)

_redis_client = None
_redis_checked = False
_redis_warned = False
REDIS_AVAILABLE: bool = False
QUERY_CACHE_PREFIX = "query:"
P = ParamSpec("P")
R = TypeVar("R")


def _warn_once(msg: str, *args: Any) -> None:
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

        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            client = Redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
        else:
            cache_enabled = os.getenv("ENABLE_REDIS_CACHE", "false").lower() == "true"
            explicit_host = os.getenv("REDIS_HOST") or os.getenv("REDIS_PORT") or os.getenv("REDIS_DB")
            if not cache_enabled and not explicit_host:
                return None
            client = Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", "6379")),
                db=int(os.getenv("REDIS_DB", "0")),
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


def get_redis_client() -> Any:
    return _get_redis()


def _mark_redis_unavailable():
    global _redis_client, REDIS_AVAILABLE
    _redis_client = None
    REDIS_AVAILABLE = False


def invalidate_query_cache(pattern: str = f"{QUERY_CACHE_PREFIX}*") -> int:
    """Delete cached query results after source data changes.

    Returns the number of cache keys Redis reports as deleted. Redis failures
    disable cache use for the current process and do not block the write path.
    """
    try:
        client = _get_redis()
        if client is None:
            return 0

        keys = list(client.scan_iter(match=pattern))
        if not keys:
            return 0
        deleted = client.delete(*keys)
        logger.info("Invalidated %s Redis query cache keys for pattern %s", deleted, pattern)
        return int(deleted or 0)
    except Exception as e:
        _warn_once("Redis cache invalidation failed, disabling caching: %s", e)
        _mark_redis_unavailable()
        return 0


def cache_query(ttl: int = 300) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator to cache results of LangGraph workflow runs.

    Gracefully degrades: if Redis is unreachable (at import, startup,
    or runtime) the wrapped function executes normally without caching.
    Never raises due to Redis unavailability. Logs a single warning.
    """
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                client = _get_redis()

                if client is None:
                    return func(*args, **kwargs)

                import hashlib
                query = args[1] if len(args) > 1 else kwargs.get("query", "")
                user_tier = args[2] if len(args) > 2 else kwargs.get("user_tier", 1)
                # Deterministic, cross-run stable cache key
                query_hash = hashlib.sha256(str(query).encode()).hexdigest()[:16]
                cache_key = f"{QUERY_CACHE_PREFIX}{query_hash}:{user_tier}"

                try:
                    cached = client.get(cache_key)
                    if cached:
                        logger.info("Cache HIT for key: %s", cache_key)
                        return cast(R, json.loads(cached))
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
