#!/usr/bin/env python3
"""Read-only trigger gate for Phase 7 sovereign cluster tasks."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

TASK_ORDER = ("P7-A", "P7-B", "P7-C", "P7-D", "P7-E", "P7-F", "P7-G", "P7-H")


@dataclass(frozen=True)
class Check:
    name: str
    ok: bool
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "ok": self.ok, "detail": self.detail}


def build_report(
    *,
    intake_bundle_dir: Path,
    qdrant_populated: bool = False,
    api_live: bool = False,
    professor_scheduled: bool = False,
    cluster_stable: bool = False,
    prior_phase_complete: bool = False,
    skip_cluster_contact: bool = False,
) -> dict[str, Any]:
    checks = [
        _command_check("kubectl"),
        _command_check("helm"),
        _command_check("sftp"),
    ]

    if skip_cluster_contact:
        checks.append(Check("kubectl_context", False, "skipped by --skip-cluster-contact"))
        checks.append(Check("cluster_info", False, "skipped by --skip-cluster-contact"))
    else:
        checks.append(_kubectl_context_check())
        checks.append(_cluster_info_check())

    checks.append(_intake_bundle_check(intake_bundle_dir))
    checks.append(
        Check(
            "intake_hmac_secret",
            bool(os.getenv("DATA_INTAKE_HMAC_SECRET")),
            "DATA_INTAKE_HMAC_SECRET present" if os.getenv("DATA_INTAKE_HMAC_SECRET") else "missing DATA_INTAKE_HMAC_SECRET",
        )
    )
    checks.append(Check("qdrant_populated", qdrant_populated, _flag_detail(qdrant_populated)))
    checks.append(Check("api_live", api_live, _flag_detail(api_live)))
    checks.append(Check("professor_scheduled", professor_scheduled, _flag_detail(professor_scheduled)))
    checks.append(Check("cluster_stable", cluster_stable, _flag_detail(cluster_stable)))
    checks.append(Check("prior_phase_complete", prior_phase_complete, _flag_detail(prior_phase_complete)))

    by_name = {check.name: check for check in checks}
    p7a_ready = all(by_name[name].ok for name in ("kubectl", "helm", "kubectl_context", "cluster_info"))
    p7b_ready = p7a_ready and by_name["sftp"].ok and by_name["intake_bundle"].ok and by_name["intake_hmac_secret"].ok
    p7c_ready = p7a_ready and qdrant_populated
    p7d_ready = p7a_ready and api_live
    p7e_ready = api_live and professor_scheduled
    p7f_ready = p7a_ready and api_live
    p7g_ready = p7a_ready and cluster_stable
    p7h_ready = all((p7a_ready, p7b_ready, p7c_ready, p7d_ready, p7e_ready, p7f_ready, p7g_ready, prior_phase_complete))

    tasks = {
        "P7-A": _task("Sovereign cluster activation", p7a_ready, "kubectl + helm + live cluster context"),
        "P7-B": _task("600GB data ingest", p7b_ready, "cluster + SFTP + manifest + HMAC ready"),
        "P7-C": _task("Vector drift baseline", p7c_ready, "Qdrant populated"),
        "P7-D": _task("C4 SLO load test", p7d_ready, "API live on cluster"),
        "P7-E": _task("UAT sessions", p7e_ready, "professor scheduled + API live"),
        "P7-F": _task("Sovereign red team", p7f_ready, "API live on cluster"),
        "P7-G": _task("DR dry run", p7g_ready, "cluster stable"),
        "P7-H": _task("Eternal seal / GPG tag", p7h_ready, "P7-A through P7-G complete"),
    }

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "ok": all(task["status"] == "READY" for task in tasks.values()),
        "checks": [check.to_dict() for check in checks],
        "tasks": tasks,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--intake-bundle-dir", type=Path, default=Path("/data/intake/2026-05-xx"))
    parser.add_argument("--qdrant-populated", action="store_true")
    parser.add_argument("--api-live", action="store_true")
    parser.add_argument("--professor-scheduled", action="store_true")
    parser.add_argument("--cluster-stable", action="store_true")
    parser.add_argument("--prior-phase-complete", action="store_true")
    parser.add_argument("--skip-cluster-contact", action="store_true")
    parser.add_argument("--require", choices=TASK_ORDER, help="Return non-zero unless this task is READY.")
    parser.add_argument("--output", type=Path, help="Optional JSON output path.")
    args = parser.parse_args(argv)

    report = build_report(
        intake_bundle_dir=args.intake_bundle_dir,
        qdrant_populated=args.qdrant_populated,
        api_live=args.api_live,
        professor_scheduled=args.professor_scheduled,
        cluster_stable=args.cluster_stable,
        prior_phase_complete=args.prior_phase_complete,
        skip_cluster_contact=args.skip_cluster_contact,
    )

    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload)
    print(payload, end="")

    if args.require and report["tasks"][args.require]["status"] != "READY":
        return 1
    return 0


def _command_check(command: str) -> Check:
    path = shutil.which(command)
    return Check(command, path is not None, path or f"{command} not found on PATH")


def _kubectl_context_check() -> Check:
    ok, output = _run(["kubectl", "config", "current-context"])
    return Check("kubectl_context", ok, output)


def _cluster_info_check() -> Check:
    ok, output = _run(["kubectl", "cluster-info"])
    return Check("cluster_info", ok, output)


def _intake_bundle_check(path: Path) -> Check:
    manifest = path / "manifest.json"
    ok = path.exists() and manifest.exists()
    detail = f"manifest present at {manifest}" if ok else f"missing intake manifest at {manifest}"
    return Check("intake_bundle", ok, detail)


def _run(command: list[str], timeout: int = 8) -> tuple[bool, str]:
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
    except Exception as exc:
        return False, str(exc)
    output = (result.stdout or result.stderr or "").strip()
    return result.returncode == 0, output[-1000:] if output else "ok"


def _task(name: str, ready: bool, trigger: str) -> dict[str, str]:
    return {"name": name, "status": "READY" if ready else "BLOCKED", "trigger": trigger}


def _flag_detail(value: bool) -> str:
    return "flag supplied" if value else "flag not supplied"


if __name__ == "__main__":
    raise SystemExit(main())
