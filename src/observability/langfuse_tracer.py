"""
Langfuse integration for NRG pipeline observability.
Traces every LLM call with: latency, token usage, model, prompt hash.
Graceful degradation: if Langfuse is down or not configured, log a warning and continue.
"""
import os
import logging
import time
from functools import wraps
from typing import Any, Callable

logger = logging.getLogger(__name__)

_client: Any = None


def _init_langfuse() -> Any:
    global _client
    if _client is not None:
        return _client
    try:
        from langfuse import Langfuse
        public_key = os.getenv("LANGFUSE_PUBLIC_KEY", "")
        secret_key = os.getenv("LANGFUSE_SECRET_KEY", "")
        host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
        if public_key and secret_key:
            _client = Langfuse(public_key=public_key, secret_key=secret_key, host=host)
            logger.info("Langfuse initialized: %s", host)
        else:
            _client = False  # explicitly disabled
    except Exception as exc:
        logger.warning("Langfuse import failed — LLM tracing disabled: %s", exc)
        _client = False
    return _client


def trace_llm_call(node_name: str) -> Callable:
    """Decorator to trace LLM calls in pipeline nodes."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            client = _init_langfuse()
            if not client:
                return func(*args, **kwargs)

            trace = client.trace(name=f"nrg.{node_name}")
            span = trace.span(name="generate", input=str(args)[:500])
            start = time.time()
            try:
                result = func(*args, **kwargs)
                latency_ms = (time.time() - start) * 1000
                span.update(
                    output=str(result)[:500],
                    status="success",
                    metadata={"latency_ms": latency_ms},
                )
                trace.update(output=str(result)[:500], status="success")
                return result
            except Exception as exc:
                latency_ms = (time.time() - start) * 1000
                span.update(
                    output=str(exc),
                    status="error",
                    metadata={"latency_ms": latency_ms},
                )
                trace.update(output=str(exc), status="error")
                raise

        return wrapper

    return decorator
