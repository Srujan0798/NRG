"""Tests for vector_drift_scheduler.py — 60s drift scheduler."""

import pytest


class TestShouldTriggerReindex:
    """Test reindex trigger policy logic."""

    def test_triggers_when_reindex_info_flag_set(self):
        from scripts.vector_drift_scheduler import should_trigger_reindex

        drift = {"alert_level": "STABLE"}
        reindex_info = {"reindex_triggered": True}
        assert should_trigger_reindex(drift, reindex_info) is True

    def test_triggers_when_max_shift_breaches_threshold(self):
        from scripts.vector_drift_scheduler import should_trigger_reindex

        drift = {"alert_level": "STABLE"}
        reindex_info = {"reindex_triggered": False, "max_shift": 0.5}
        with pytest.MonkeyPatch.context():
            import scripts.vector_drift_scheduler as vds
            orig = vds.COSINE_SHIFT_THRESHOLD
            vds.COSINE_SHIFT_THRESHOLD = 0.3
            try:
                result = should_trigger_reindex(drift, reindex_info)
                assert result is True
            finally:
                vds.COSINE_SHIFT_THRESHOLD = orig

    def test_triggers_when_drift_alert_warning(self):
        from scripts.vector_drift_scheduler import should_trigger_reindex

        drift = {"alert_level": "WARNING"}
        reindex_info = {"reindex_triggered": False}
        assert should_trigger_reindex(drift, reindex_info) is True

    def test_triggers_when_drift_alert_critical(self):
        from scripts.vector_drift_scheduler import should_trigger_reindex

        drift = {"alert_level": "CRITICAL"}
        reindex_info = {"reindex_triggered": False}
        assert should_trigger_reindex(drift, reindex_info) is True

    def test_no_trigger_when_stable_and_no_flags(self):
        from scripts.vector_drift_scheduler import should_trigger_reindex

        drift = {"alert_level": "STABLE"}
        reindex_info = {"reindex_triggered": False, "max_shift": 0.01}
        assert should_trigger_reindex(drift, reindex_info) is False


@pytest.mark.asyncio
async def test_run_once_calls_check_fn():
    from scripts.vector_drift_scheduler import run_once

    mock_check = {"drift": {"alert_level": "STABLE"}, "reindex_info": {"reindex_triggered": False}}
    result = await run_once(check_fn=lambda: mock_check, reindex_fn=lambda *a: None)
    assert result.drift["alert_level"] == "STABLE"
    assert result.reindex_triggered is False


@pytest.mark.asyncio
async def test_run_once_triggers_reindex_when_needed():
    from scripts.vector_drift_scheduler import run_once

    mock_check = {"drift": {"alert_level": "CRITICAL"}, "reindex_info": {"reindex_triggered": True}}
    triggered = False

    def mock_reindex(d, r):
        nonlocal triggered
        triggered = True

    result = await run_once(check_fn=lambda: mock_check, reindex_fn=mock_reindex)
    assert result.reindex_triggered is True
    assert triggered is True


@pytest.mark.asyncio
async def test_run_once_no_trigger_when_stable():
    from scripts.vector_drift_scheduler import run_once

    mock_check = {"drift": {"alert_level": "STABLE"}, "reindex_info": {"reindex_triggered": False}}
    triggered = False

    def mock_reindex(d, r):
        nonlocal triggered
        triggered = True

    result = await run_once(check_fn=lambda: mock_check, reindex_fn=mock_reindex)
    assert result.reindex_triggered is False
    assert triggered is False


@pytest.mark.asyncio
async def test_loop_runs_max_iterations():
    calls = []

    async def mock_sleep(n):
        calls.append(n)

    mock_check = {"drift": {"alert_level": "STABLE"}, "reindex_info": {"reindex_triggered": False}}

    from scripts.vector_drift_scheduler import scheduler_loop

    runs = await scheduler_loop(
        interval_seconds=60,
        check_fn=lambda: mock_check,
        reindex_fn=lambda *a: None,
        sleep_fn=mock_sleep,
        max_iterations=3,
    )
    assert len(runs) == 3
    assert len(calls) == 2


@pytest.mark.asyncio
async def test_loop_returns_schedulerrun_list():
    from scripts.vector_drift_scheduler import scheduler_loop, SchedulerRun

    mock_check = {"drift": {"alert_level": "STABLE"}, "reindex_info": {"reindex_triggered": False}}

    runs = await scheduler_loop(
        interval_seconds=60,
        check_fn=lambda: mock_check,
        reindex_fn=lambda *a: None,
        sleep_fn=lambda n: None,
        max_iterations=1,
    )
    assert len(runs) == 1
    assert isinstance(runs[0], SchedulerRun)


@pytest.mark.asyncio
async def test_interval_must_be_positive():
    from scripts.vector_drift_scheduler import scheduler_loop

    with pytest.raises(ValueError, match="interval_seconds must be positive"):
        await scheduler_loop(interval_seconds=0, max_iterations=1, sleep_fn=lambda n: None)
