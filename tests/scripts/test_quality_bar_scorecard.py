from types import SimpleNamespace

import scripts.quality_bar_scorecard as scorecard


def test_c5_uses_scheduler_dry_run_when_live_qdrant_is_unavailable(monkeypatch):
    calls: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        calls.append([str(part) for part in cmd])
        command = " ".join(str(part) for part in cmd)
        if "vector_drift_check.py" in command:
            return SimpleNamespace(
                returncode=2,
                stdout="VECTOR DRIFT CHECK SKIPPED\nqdrant_unavailable\n",
                stderr="",
            )
        if "vector_drift_scheduler.py" in command:
            return SimpleNamespace(
                returncode=0,
                stdout=(
                    '{"status":"dry_run","interval_seconds":60,'
                    '"cosine_shift_threshold":0.05,'
                    '"reindex_endpoint":"/api/reindex"}'
                ),
                stderr="",
            )
        raise AssertionError(f"unexpected command: {command}")

    monkeypatch.setattr(scorecard.subprocess, "run", fake_run)

    result = scorecard._run_drift_check()

    assert result["status"] == "pass"
    assert result["passed"] == 1
    assert result["passed_rate"] == 1.0
    assert result["live_qdrant_skipped"] is True
    assert result["scheduler_interval_seconds"] == 60
    assert result["scheduler_reindex_endpoint"] == "/api/reindex"
    assert any("vector_drift_scheduler.py" in " ".join(call) for call in calls)
