"""Tests for the 60-second vector drift scheduler."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).parent.parent.parent / "scripts" / "vector_drift_scheduler.py"
SCRIPTS_DIR = str(SCRIPT_PATH.parent)
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)
_spec = importlib.util.spec_from_file_location("vector_drift_scheduler", SCRIPT_PATH)
_scheduler = importlib.util.module_from_spec(_spec)
sys.modules["vector_drift_scheduler"] = _scheduler
_spec.loader.exec_module(_scheduler)


def test_default_interval_is_60_seconds():
    assert _scheduler.DEFAULT_INTERVAL_SECONDS == 60


@pytest.mark.asyncio
async def test_scheduler_sleeps_for_configured_60_second_interval():
    sleeps: list[float] = []

    async def fake_sleep(seconds: float):
        sleeps.append(seconds)

    runs = await _scheduler.scheduler_loop(
        interval_seconds=60,
        max_iterations=2,
        check_fn=lambda: {
            "drift": {"alert_level": "GREEN", "drift_score": 0.92},
            "reindex_info": {"reindex_triggered": False},
        },
        reindex_fn=lambda *_: None,
        sleep_fn=fake_sleep,
    )

    assert len(runs) == 2
    assert sleeps == [60]


@pytest.mark.asyncio
async def test_scheduler_triggers_reindex_on_cosine_shift_breach():
    triggered: list[tuple[dict, dict]] = []

    run = await _scheduler.run_once(
        check_fn=lambda: {
            "drift": {"alert_level": "GREEN", "drift_score": 0.9},
            "reindex_info": {
                "status": "cosine_shift_detected",
                "max_shift": 0.06,
                "reindex_triggered": False,
            },
        },
        reindex_fn=lambda drift, info: triggered.append((drift, info)),
    )

    assert run.reindex_triggered is True
    assert triggered
    assert triggered[0][1]["max_shift"] == 0.06


@pytest.mark.asyncio
async def test_scheduler_does_not_reindex_when_stable():
    triggered: list[tuple[dict, dict]] = []

    run = await _scheduler.run_once(
        check_fn=lambda: {
            "drift": {"alert_level": "GREEN", "drift_score": 0.91},
            "reindex_info": {"status": "stable", "max_shift": 0.01},
        },
        reindex_fn=lambda drift, info: triggered.append((drift, info)),
    )

    assert run.reindex_triggered is False
    assert triggered == []
