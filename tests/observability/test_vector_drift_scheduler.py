"""Tests for the 60-second vector drift scheduler."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

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


def test_main_without_args_runs_one_drift_check_without_crash(monkeypatch):
    calls: list[dict] = []

    async def fake_loop(**kwargs):
        calls.append(kwargs)
        return []

    monkeypatch.setattr(sys, "argv", ["vector_drift_scheduler.py"])
    monkeypatch.setattr(_scheduler, "scheduler_loop", fake_loop)

    assert _scheduler.main() == 0
    assert calls[0]["max_iterations"] == 1


def test_default_check_establishes_baseline_before_drift_check(monkeypatch, tmp_path):
    calls: list[list[str]] = []

    def fake_runner(command, **kwargs):
        calls.append(command)
        return SimpleNamespace(returncode=0, stdout="{}", stderr="")

    monkeypatch.setattr(_scheduler, "BASELINE_MARKER_FILE", tmp_path / "baseline.ok")
    monkeypatch.setattr(_scheduler, "Retriever", lambda timeout=5.0: object())
    monkeypatch.setattr(
        _scheduler,
        "run_health_check",
        lambda retriever: {
            "status": "ok",
            "indexed_vectors": 10,
            "total_vectors": 10,
            "coverage_pct": 100.0,
            "latency_ms": 1,
        },
    )
    monkeypatch.setattr(
        _scheduler,
        "run_drift_check",
        lambda retriever, verbose=False: {"alert_level": "GREEN", "drift_score": 0.9},
    )

    result = _scheduler._default_check(command_runner=fake_runner)

    assert result["drift"]["alert_level"] == "GREEN"
    assert calls
    assert "scripts/vector_drift_check.py" in " ".join(calls[0])
    assert "--establish-baseline" in calls[0]


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
async def test_scheduler_emits_retrain_event_on_threshold_breach():
    emitted: list[tuple[dict, dict]] = []

    run = await _scheduler.run_once(
        check_fn=lambda: {
            "drift": {"alert_level": "CRITICAL", "drift_score": 0.31},
            "reindex_info": {
                "status": "benchmark_drift_detected",
                "reindex_triggered": True,
            },
        },
        reindex_fn=lambda drift, info: emitted.append((drift, info)),
    )

    assert run.reindex_triggered is True
    assert emitted == [
        (
            {"alert_level": "CRITICAL", "drift_score": 0.31},
            {"status": "benchmark_drift_detected", "reindex_triggered": True},
        )
    ]


def test_cron_manifest_exists_without_inline_secrets():
    manifest_path = (
        Path(__file__).parent.parent.parent
        / "infrastructure"
        / "cron"
        / "nrg-drift-monitor"
        / "cronjob.yaml"
    )

    assert manifest_path.exists()
    docs = list(yaml.safe_load_all(manifest_path.read_text()))
    cronjob = next(doc for doc in docs if doc["kind"] == "CronJob")

    assert cronjob["metadata"]["name"] == "nrg-drift-monitor"
    command = "\n".join(
        cronjob["spec"]["jobTemplate"]["spec"]["template"]["spec"]["containers"][0]["command"]
    )
    assert "scripts/vector_drift_scheduler.py --once" in command
    source = manifest_path.read_text()
    assert "secretKeyRef" in source
    assert "Bearer " not in source
    assert "password" not in manifest_path.read_text().lower()


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
