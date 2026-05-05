"""Bounded async bridge for request-path audit-chain appends."""

from __future__ import annotations

import asyncio
import atexit
import os
import queue
import threading
from concurrent.futures import Future
from typing import Any, Callable

_AuditAppendJob = tuple[Future[Any], Callable[..., Any], tuple[Any, ...], dict[str, Any]]
_work_queue: queue.Queue[_AuditAppendJob | None] | None = None
_workers: list[threading.Thread] = []
_stop_event: threading.Event | None = None
_executor_lock = threading.Lock()


def _configured_queue_size() -> int:
    raw_value = os.getenv("NRG_AUDIT_APPEND_QUEUE_SIZE", "4096")
    try:
        return max(1, int(raw_value))
    except (TypeError, ValueError):
        return 4096


def _configured_workers() -> int:
    raw_value = os.getenv("NRG_AUDIT_APPEND_WORKERS", "1")
    try:
        return max(1, int(raw_value))
    except (TypeError, ValueError):
        return 1


def _audit_append_worker(work_queue: queue.Queue[_AuditAppendJob | None], stop_event: threading.Event) -> None:
    while not stop_event.is_set():
        job = work_queue.get()
        try:
            if job is None:
                return
            future, fn, args, kwargs = job
            if not future.set_running_or_notify_cancel():
                continue
            try:
                future.set_result(fn(*args, **kwargs))
            except Exception as exc:
                future.set_exception(exc)
        finally:
            work_queue.task_done()


def get_audit_append_executor() -> queue.Queue[_AuditAppendJob | None]:
    """Return the bounded daemon-worker queue used for request-path audit appends."""
    global _work_queue, _workers, _stop_event
    with _executor_lock:
        live_workers = [worker for worker in _workers if worker.is_alive()]
        if _work_queue is None or len(live_workers) != _configured_workers():
            if _stop_event is not None:
                _stop_event.set()
            for _ in live_workers:
                try:
                    _work_queue.put_nowait(None)  # type: ignore[union-attr]
                except Exception:
                    pass
            _work_queue = queue.Queue(maxsize=_configured_queue_size())
            _stop_event = threading.Event()
            _workers = []
            for index in range(_configured_workers()):
                worker = threading.Thread(
                    target=_audit_append_worker,
                    args=(_work_queue, _stop_event),
                    name=f"audit_append_{index}",
                    daemon=True,
                )
                worker.start()
                _workers.append(worker)
        return _work_queue


async def _await_concurrent_future(future: Future[Any]) -> Any:
    wrapped = asyncio.wrap_future(future)
    try:
        return await wrapped
    except asyncio.CancelledError:
        future.cancel()
        raise


def _enqueue_audit_append(
    future: Future[Any],
    fn: Callable[..., Any],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> None:
    work_queue = get_audit_append_executor()
    try:
        work_queue.put_nowait(
            (
                future,
                fn,
                args,
                kwargs,
            )
        )
    except queue.Full:
        future.set_exception(RuntimeError("Audit append queue is full"))


async def run_audit_append(fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """Run an audit append in the bounded audit worker queue and await its result."""
    future: Future[Any] = Future()
    loop = asyncio.get_running_loop()
    loop.call_soon(_enqueue_audit_append, future, fn, args, kwargs)
    return await _await_concurrent_future(future)


def shutdown_audit_append_executor(*, final: bool = False) -> None:
    """Stop the bounded audit executor during app shutdown or tests."""
    global _work_queue, _workers, _stop_event
    with _executor_lock:
        work_queue = _work_queue
        workers = list(_workers)
        stop_event = _stop_event
        _work_queue = None
        _workers = []
        _stop_event = None
    if stop_event is not None:
        stop_event.set()
    if work_queue is not None:
        for _ in workers:
            try:
                work_queue.put_nowait(None)
            except Exception:
                pass
    if not final:
        get_audit_append_executor()


atexit.register(lambda: shutdown_audit_append_executor(final=True))
