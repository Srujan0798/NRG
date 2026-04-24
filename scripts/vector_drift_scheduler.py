#!/usr/bin/env python3
"""60-second vector drift scheduler for C5 detect-to-emit monitoring."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Awaitable, Callable, Optional

from vector_drift_check import (
    COSINE_SHIFT_THRESHOLD,
    _trigger_reindex,
    run_drift_check,
    run_health_check,
)
from src.skills.rag.retriever import Retriever

DEFAULT_INTERVAL_SECONDS = 60

logger = logging.getLogger("vector_drift_scheduler")

DriftCheckFn = Callable[[], dict]
ReindexFn = Callable[[dict, dict], None]
SleepFn = Callable[[float], Awaitable[None]]


@dataclass(frozen=True)
class SchedulerRun:
    """Result from one scheduled drift pass."""

    drift: dict
    reindex_info: dict
    reindex_triggered: bool


def _default_check() -> dict:
    """Run the real drift check once."""
    retriever = Retriever(timeout=5.0)
    health = run_health_check(retriever)
    if health.get("status") not in {"ok", "degraded"}:
        return {
            "drift": {"alert_level": "UNKNOWN", "drift_score": 0.0},
            "reindex_info": {
                "status": "qdrant_unavailable",
                "reindex_triggered": False,
                "qdrant": health,
            },
        }
    drift = run_drift_check(retriever, verbose=False)
    return {
        "drift": drift,
        "reindex_info": {
            "status": "benchmark_drift_detected"
            if drift.get("alert_level") in {"WARNING", "CRITICAL"}
            else "stable",
            "reindex_triggered": drift.get("alert_level") in {"WARNING", "CRITICAL"},
        },
    }


def should_trigger_reindex(drift: dict, reindex_info: dict) -> bool:
    """Return True when drift/cosine shift breaches the reindex policy."""
    if reindex_info.get("reindex_triggered"):
        return True
    if reindex_info.get("max_shift", 0) > COSINE_SHIFT_THRESHOLD:
        return True
    return drift.get("alert_level") in {"WARNING", "CRITICAL"}


async def run_once(
    check_fn: Optional[DriftCheckFn] = None,
    reindex_fn: ReindexFn = _trigger_reindex,
) -> SchedulerRun:
    """Run one drift-check pass and emit `/api/reindex` when policy breaches."""
    check = check_fn or _default_check
    result = check()
    drift = result.get("drift", result)
    reindex_info = result.get("reindex_info", {})
    triggered = should_trigger_reindex(drift, reindex_info)
    if triggered:
        reindex_fn(drift, reindex_info)
    return SchedulerRun(
        drift=drift,
        reindex_info=reindex_info,
        reindex_triggered=triggered,
    )


async def scheduler_loop(
    interval_seconds: int = DEFAULT_INTERVAL_SECONDS,
    check_fn: Optional[DriftCheckFn] = None,
    reindex_fn: ReindexFn = _trigger_reindex,
    sleep_fn: SleepFn = asyncio.sleep,
    max_iterations: Optional[int] = None,
) -> list[SchedulerRun]:
    """Run the 60-second drift scheduler until stopped or max_iterations is hit."""
    if interval_seconds <= 0:
        raise ValueError("interval_seconds must be positive")

    runs: list[SchedulerRun] = []
    iteration = 0
    while max_iterations is None or iteration < max_iterations:
        iteration += 1
        run = await run_once(check_fn=check_fn, reindex_fn=reindex_fn)
        runs.append(run)
        logger.info(
            "drift_scheduler iteration=%s alert=%s reindex_triggered=%s",
            iteration,
            run.drift.get("alert_level"),
            run.reindex_triggered,
        )
        if max_iterations is not None and iteration >= max_iterations:
            break
        await sleep_fn(interval_seconds)
    return runs


def main() -> int:
    parser = argparse.ArgumentParser(description="NRG 60-second vector drift scheduler")
    parser.add_argument("--interval-seconds", type=int, default=DEFAULT_INTERVAL_SECONDS)
    parser.add_argument("--once", action="store_true", help="Run one real check and exit")
    parser.add_argument("--dry-run", action="store_true", help="Print scheduler config and exit")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    if args.dry_run:
        print(json.dumps({
            "status": "dry_run",
            "interval_seconds": args.interval_seconds,
            "cosine_shift_threshold": COSINE_SHIFT_THRESHOLD,
            "reindex_endpoint": "/api/reindex",
        }, indent=2))
        return 0

    asyncio.run(
        scheduler_loop(
            interval_seconds=args.interval_seconds,
            max_iterations=1 if args.once else None,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
