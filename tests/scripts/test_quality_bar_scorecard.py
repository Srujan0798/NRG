import socket
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


def test_c4_scorecard_creates_locust_report_parent(monkeypatch, tmp_path):
    class FakeSocket:
        def settimeout(self, _timeout):
            return None

        def connect(self, _address):
            return None

        def close(self):
            return None

    def fake_run(cmd, **kwargs):
        assert (tmp_path / ".cache").is_dir()
        assert str(tmp_path / ".cache" / "locust_report.html") in [str(part) for part in cmd]
        assert "LOAD_TEST_RESEARCHER_TOKEN" in kwargs["env"]
        assert "LOAD_TEST_GOV_TOKEN" in kwargs["env"]
        return SimpleNamespace(
            returncode=0,
            stdout=(
                "Total samples : 1,250\n"
                "P99           :      320.0 ms  <- C4 SLO target < 500 ms\n"
                "Aggregated 1250 0(0.00%) | 150 5 400 120 | 100.00 0.00\n"
                "C4 PASS - P99 320.0ms < 500ms SLO\n"
            ),
            stderr="",
        )

    monkeypatch.setattr(scorecard, "ROOT", tmp_path)
    monkeypatch.setattr(socket, "socket", lambda *_args, **_kwargs: FakeSocket())
    monkeypatch.setattr(
        scorecard,
        "_preissue_load_tokens",
        lambda _host: {
            "LOAD_TEST_RESEARCHER_TOKEN": "researcher-token",
            "LOAD_TEST_GOV_TOKEN": "gov-token",
        },
    )
    monkeypatch.setattr(scorecard.subprocess, "run", fake_run)

    result = scorecard._run_c4_load_test()

    assert result["passed"] == 1
    assert result["exit_code"] == 0
    assert result["p99_ms"] == 320.0
    assert result["preissued_tokens"] == ["LOAD_TEST_GOV_TOKEN", "LOAD_TEST_RESEARCHER_TOKEN"]


def test_c4_scorecard_can_run_locust_with_multiple_processes(monkeypatch, tmp_path):
    class FakeSocket:
        def settimeout(self, _timeout):
            return None

        def connect(self, _address):
            return None

        def close(self):
            return None

    def fake_run(cmd, **kwargs):
        assert "--processes" in cmd
        assert cmd[cmd.index("--processes") + 1] == "4"
        return SimpleNamespace(
            returncode=0,
            stdout=(
                "Total samples : 1,250\n"
                "P99           :      320.0 ms  <- C4 SLO target < 500 ms\n"
                "Aggregated 1250 0(0.00%) | 150 5 400 120 | 100.00 0.00\n"
                "C4 PASS - P99 320.0ms < 500ms SLO\n"
            ),
            stderr="",
        )

    monkeypatch.setattr(scorecard, "ROOT", tmp_path)
    monkeypatch.setattr(scorecard, "LOCUST_PROCESSES", 4, raising=False)
    monkeypatch.setattr(socket, "socket", lambda *_args, **_kwargs: FakeSocket())
    monkeypatch.setattr(
        scorecard,
        "_preissue_load_tokens",
        lambda _host: {"LOAD_TEST_RESEARCHER_TOKEN": "researcher-token"},
    )
    monkeypatch.setattr(scorecard.subprocess, "run", fake_run)

    result = scorecard._run_c4_load_test()

    assert result["passed"] == 1
    assert result["locust_processes"] == 4


def test_c4_scorecard_rejects_target_text_without_numeric_p99():
    metrics = scorecard._extract_c4_metrics(
        "1000 users\n"
        "P99 target < 500ms\n"
        "Aggregated 1000 0(0.00%) | 100 5 300 100 | 50.00 0.00\n"
    )

    assert metrics["p99_ms"] is None
    assert metrics["p99_ok"] is False


def test_c4_scorecard_rejects_failure_rate_above_zero():
    metrics = scorecard._extract_c4_metrics(
        "Total samples : 1,000\n"
        "P99           :      300.0 ms  <- C4 SLO target < 500 ms\n"
        "Aggregated 1000 2(0.20%) | 100 5 300 100 | 50.00 0.10\n"
        "C4 PASS - P99 300.0ms < 500ms SLO\n"
    )

    assert metrics["p99_ok"] is True
    assert metrics["failure_rate"] == 0.002
    assert metrics["failure_rate_ok"] is False


def test_c4_scorecard_extracts_locust_percentile_table_when_summary_is_missing():
    metrics = scorecard._extract_c4_metrics(
        "Aggregated 90716 78523(86.56%) | 2500 1 8173 2400 | 302.85 262.15\n"
        "Response time percentiles (approximated)\n"
        "Type Name 50% 66% 75% 80% 90% 95% 98% 99% 99.9% 99.99% 100% # reqs\n"
        "Aggregated 2400 2800 3000 3200 3800 4600 5400 5900 6900 7900 8200 90716\n"
    )

    assert metrics["p99_ms"] == 5900.0
    assert metrics["total_samples"] == 90716
    assert metrics["p99_ok"] is False
    assert metrics["sample_count_ok"] is True


def test_c4_scorecard_reads_numeric_p99_from_locust_report(tmp_path):
    report = tmp_path / "locust_report.html"
    report.write_text(
        '"requests_statistics": ['
        '{"avg_content_length": 1.0, "avg_response_time": 10.0, '
        '"name": "Aggregated", "num_failures": 0, "num_requests": 1000, '
        '"response_time_percentile_0.99": 420.0}'
        ']'
    )

    metrics = scorecard._extract_c4_metrics("", report_path=report)

    assert metrics["p99_ms"] == 420.0
    assert metrics["total_samples"] == 1000
    assert metrics["failure_rate"] == 0.0
    assert metrics["p99_ok"] is True


def test_c4_scorecard_reads_per_endpoint_metrics_from_locust_report(tmp_path):
    report = tmp_path / "locust_report.html"
    report.write_text(
        '"requests_statistics": ['
        '{"avg_content_length": 1.0, "avg_response_time": 10.0, '
        '"name": "/query::researcher", "num_failures": 0, "num_requests": 900, '
        '"response_time_percentile_0.99": 240.0},'
        '{"avg_content_length": 1.0, "avg_response_time": 20.0, '
        '"name": "/query::adversarial", "num_failures": 3, "num_requests": 100, '
        '"response_time_percentile_0.99": 900.0},'
        '{"avg_content_length": 1.0, "avg_response_time": 12.0, '
        '"name": "Aggregated", "num_failures": 3, "num_requests": 1000, '
        '"response_time_percentile_0.99": 900.0}'
        ']'
    )

    metrics = scorecard._extract_c4_metrics("", report_path=report)

    assert metrics["failure_rate"] == 0.003
    assert metrics["endpoint_metrics"] == {
        "/query::researcher": {
            "num_requests": 900,
            "num_failures": 0,
            "failure_rate": 0.0,
            "p99_ms": 240.0,
        },
        "/query::adversarial": {
            "num_requests": 100,
            "num_failures": 3,
            "failure_rate": 0.03,
            "p99_ms": 900.0,
        },
    }


def test_c4_scorecard_ignores_response_percentile_objects_without_request_counts(tmp_path):
    report = tmp_path / "locust_report.html"
    report.write_text(
        '"requests_statistics": ['
        '{"name": "/query::researcher", "num_failures": 0, "num_requests": 900, '
        '"response_time_percentile_0.99": 240.0},'
        '{"name": "Aggregated", "num_failures": 0, "num_requests": 900, '
        '"response_time_percentile_0.99": 240.0}'
        '],'
        '"response_time_statistics": ['
        '{"0.99": 300.0, "method": "POST", "name": "/query::researcher"},'
        '{"0.99": 300.0, "method": "", "name": "Aggregated"}'
        ']'
    )

    metrics = scorecard._extract_c4_metrics("", report_path=report)

    assert metrics["p99_ms"] == 240.0
    assert metrics["total_samples"] == 900
    assert metrics["failure_rate"] == 0.0
    assert metrics["endpoint_metrics"]["/query::researcher"] == {
        "num_requests": 900,
        "num_failures": 0,
        "failure_rate": 0.0,
        "p99_ms": 240.0,
    }


def test_c4_locustfile_preissued_token_path_does_not_send_forwarded_ip():
    source = scorecard.ROOT.joinpath("tests/load/locustfile_c4.py").read_text()
    token_branch = source.split("if token:", 1)[1].split("return", 1)[0]

    assert '"Authorization": f"Bearer {token}"' in token_branch
    assert "X-Forwarded-For" not in token_branch
