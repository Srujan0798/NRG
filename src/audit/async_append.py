"""Bounded async bridge for request-path audit-chain appends."""

from __future__ import annotations

import asyncio
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import Any, Callable

_executor: ThreadPoolExecutor | None = None
_executor_lock = threading.Lock()


def _configured_workers() -> int:
    raw_value = os.getenv("NRG_AUDIT_APPEND_WORKERS", "1")
    try:
        return max(1, int(raw_value))
    except (TypeError, ValueError):
        return 1


def get_audit_append_executor() -> ThreadPoolExecutor:
    """Return the bounded executor used for request-path audit appends."""
    global _executor
    with _executor_lock:
        if _executor is None:
            _executor = ThreadPoolExecutor(
                max_workers=_configured_workers(),
                thread_name_prefix="audit_append",
            )
        return _executor


async def run_audit_append(fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """Run an audit append in the bounded audit executor and await its result."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        get_audit_append_executor(),
        partial(fn, *args, **kwargs),
    )


def shutdown_audit_append_executor() -> None:
    """Stop the bounded audit executor during app shutdown or tests."""
    global _executor
    with _executor_lock:
        executor = _executor
        _executor = None
    if executor is not None:
        executor.shutdown(wait=False, cancel_futures=True)
