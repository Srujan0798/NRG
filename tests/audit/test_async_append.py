import asyncio
import threading
import time

import pytest

from src.audit import async_append


@pytest.mark.asyncio
async def test_audit_append_executor_serializes_by_default(monkeypatch):
    async_append.shutdown_audit_append_executor()
    monkeypatch.setenv("NRG_AUDIT_APPEND_WORKERS", "1")

    active = 0
    max_active = 0
    lock = threading.Lock()

    def work(index: int) -> int:
        nonlocal active, max_active
        with lock:
            active += 1
            max_active = max(max_active, active)
        time.sleep(0.01)
        with lock:
            active -= 1
        return index

    try:
        results = await asyncio.gather(
            *(async_append.run_audit_append(work, index) for index in range(8))
        )
    finally:
        async_append.shutdown_audit_append_executor()

    assert sorted(results) == list(range(8))
    assert max_active == 1
