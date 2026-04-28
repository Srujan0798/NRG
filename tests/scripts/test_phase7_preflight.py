from __future__ import annotations

import os

from scripts import phase7_preflight


def test_phase7_preflight_blocks_without_helm(monkeypatch, tmp_path):
    def fake_which(command: str) -> str | None:
        return "/usr/bin/kubectl" if command in {"kubectl", "sftp"} else None

    monkeypatch.setattr(phase7_preflight.shutil, "which", fake_which)
    monkeypatch.setattr(phase7_preflight, "_run", lambda *args, **kwargs: (True, "ok"))

    report = phase7_preflight.build_report(
        intake_bundle_dir=tmp_path / "missing",
        qdrant_populated=False,
        api_live=False,
        professor_scheduled=False,
        cluster_stable=False,
        prior_phase_complete=False,
    )

    assert report["tasks"]["P7-A"]["status"] == "BLOCKED"
    assert any(check["name"] == "helm" and check["ok"] is False for check in report["checks"])


def test_phase7_preflight_marks_triggers_ready(monkeypatch, tmp_path):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "manifest.json").write_text("{}")

    monkeypatch.setattr(phase7_preflight.shutil, "which", lambda command: f"/usr/bin/{command}")
    monkeypatch.setattr(phase7_preflight, "_run", lambda *args, **kwargs: (True, "ok"))
    monkeypatch.setitem(os.environ, "DATA_INTAKE_HMAC_SECRET", "x" * 32)

    report = phase7_preflight.build_report(
        intake_bundle_dir=bundle,
        qdrant_populated=True,
        api_live=True,
        professor_scheduled=True,
        cluster_stable=True,
        prior_phase_complete=True,
    )

    assert all(task["status"] == "READY" for task in report["tasks"].values())


def test_cli_require_returns_nonzero_when_task_blocked(monkeypatch, tmp_path):
    monkeypatch.setattr(phase7_preflight.shutil, "which", lambda command: None)

    exit_code = phase7_preflight.main(
        [
            "--require",
            "P7-A",
            "--intake-bundle-dir",
            str(tmp_path / "missing"),
        ]
    )

    assert exit_code == 1
