#!/usr/bin/env python3
"""Run or stage the remaining external NRG production gates.

This runner deliberately separates local evidence from external proof. It will
execute a gate only when the required deployment/cluster/signing inputs are
present. Otherwise it writes a BLOCKED row with the exact missing inputs and the
command to run when the environment is available.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVIDENCE_DIR = REPO_ROOT / "evidence" / time.strftime("%Y-%m-%d") / "final_external_gates"
HANDOVER_DOCS = [
    REPO_ROOT / "docs/handover/README.md",
    REPO_ROOT / "docs/handover/SYSTEM_OVERVIEW.md",
    REPO_ROOT / "docs/handover/ARCHITECTURE.md",
    REPO_ROOT / "docs/handover/API_REFERENCE.md",
    REPO_ROOT / "docs/handover/OPERATIONS_RUNBOOK.md",
    REPO_ROOT / "docs/handover/SECURITY_COMPLIANCE_ATTESTATION.md",
    REPO_ROOT / "docs/handover/DATA_INTAKE_PROTOCOL.md",
    REPO_ROOT / "docs/handover/UAT_RESULTS.md",
]
LOCAL_KUBE_CONTEXTS = {"colima", "docker-desktop", "minikube", "rancher-desktop"}


def _redacted_env(name: str) -> str:
    return "set" if os.getenv(name) else "missing"


def _run(
    command: list[str],
    *,
    cwd: Path = REPO_ROOT,
    env: dict[str, str] | None = None,
    timeout: int = 900,
    output: Path | None = None,
) -> dict:
    started = time.time()
    proc = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(proc.stdout)
    return {
        "command": " ".join(command),
        "exit_code": proc.returncode,
        "duration_ms": int((time.time() - started) * 1000),
        "output": str(output) if output else None,
    }


def _fetch_json(url: str, output: Path) -> dict:
    req = Request(url, headers={"Accept": "application/json"})
    with urlopen(req, timeout=20) as response:
        body = response.read().decode("utf-8", errors="replace")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(body)
    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        parsed = {"raw": body}
    return {
        "url": url,
        "output": str(output),
        "payload": parsed,
    }


def _gate(status: str, name: str, **extra) -> dict:
    return {"gate": name, "status": status, **extra}


def _is_local_kube_context(context: str) -> bool:
    normalized = context.strip().lower()
    return normalized in LOCAL_KUBE_CONTEXTS or normalized.startswith("kind-")


def _allowed_kube_contexts() -> set[str]:
    raw = os.getenv("NRG_ALLOWED_CLUSTER_CONTEXTS", "")
    return {item.strip() for item in raw.split(",") if item.strip()}


def _cluster_context_preflight(evidence_dir: Path) -> dict | None:
    """Block cluster load proof unless the context is explicit and non-local."""
    checks: dict[str, dict | str] = {"KUBECONFIG": _redacted_env("KUBECONFIG")}
    missing = []

    if not os.getenv("KUBECONFIG"):
        missing.append("KUBECONFIG")

    current = _run(
        ["kubectl", "config", "current-context"],
        timeout=30,
        output=evidence_dir / "kubectl_current_context.log",
    )
    checks["current_context"] = current
    context = ""
    if current["exit_code"] == 0:
        context = (evidence_dir / "kubectl_current_context.log").read_text().strip()
        checks["current_context_name"] = context
        if _is_local_kube_context(context):
            missing.append(f"non-local Kubernetes context required; current context is {context}")
    else:
        missing.append("current Kubernetes context")

    allowed_contexts = _allowed_kube_contexts()
    if allowed_contexts and context and context not in allowed_contexts:
        missing.append(
            "current Kubernetes context is not in NRG_ALLOWED_CLUSTER_CONTEXTS"
        )
        checks["allowed_contexts"] = sorted(allowed_contexts)

    if missing:
        return _gate(
            "BLOCKED",
            "sovereign_cluster_1000_user_load",
            missing=missing,
            checks=checks,
            run_when_ready=(
                "KUBECONFIG=/path/to/sovereign-cluster "
                "NRG_ALLOWED_CLUSTER_CONTEXTS=sovereign-staging "
                "python scripts/run_final_external_gates.py --run-cluster-load"
            ),
        )
    return None


def deployed_browser_gate(evidence_dir: Path) -> dict:
    frontend_url = os.getenv("NRG_DEPLOYED_FRONTEND_URL")
    api_url = os.getenv("NRG_DEPLOYED_API_URL") or os.getenv("NRG_PRODUCTION_API_URL")
    if not frontend_url or not api_url:
        return _gate(
            "BLOCKED",
            "deployed_browser_replay",
            missing=[
                name
                for name, value in {
                    "NRG_DEPLOYED_FRONTEND_URL": frontend_url,
                    "NRG_DEPLOYED_API_URL or NRG_PRODUCTION_API_URL": api_url,
                }.items()
                if not value
            ],
            run_when_ready=(
                "cd frontend && "
                "NRG_DEPLOYED_FRONTEND_URL=https://... "
                "NRG_DEPLOYED_API_URL=https://... "
                "NRG_EVIDENCE_DIR=../evidence/YYYY-MM-DD/final_external_gates/deployed_browser "
                "npx playwright test tests/e2e/deployed_final_gate.spec.ts --reporter=list"
            ),
        )

    browser_dir = evidence_dir / "deployed_browser"
    env = os.environ.copy()
    env["NRG_DEPLOYED_FRONTEND_URL"] = frontend_url
    env["NRG_DEPLOYED_API_URL"] = api_url
    env["NRG_EVIDENCE_DIR"] = f"../{browser_dir.relative_to(REPO_ROOT)}"
    result = _run(
        ["npx", "playwright", "test", "-c", "tests/playwright.deployed.config.ts", "--reporter=list"],
        cwd=REPO_ROOT / "frontend",
        env=env,
        timeout=300,
        output=evidence_dir / "deployed_browser_replay.log",
    )
    status = "PASS" if result["exit_code"] == 0 else "FAIL"
    return _gate(status, "deployed_browser_replay", result=result, evidence_dir=str(browser_dir))


def qdrant_baseline_gate(evidence_dir: Path) -> dict:
    api_url = (os.getenv("NRG_PRODUCTION_API_URL") or os.getenv("NRG_DEPLOYED_API_URL") or "").rstrip("/")
    if not api_url:
        return _gate(
            "BLOCKED",
            "production_qdrant_baseline",
            missing=["NRG_PRODUCTION_API_URL or NRG_DEPLOYED_API_URL"],
            run_when_ready="NRG_PRODUCTION_API_URL=https://api... python scripts/run_final_external_gates.py",
        )

    outputs = []
    errors = []
    for endpoint in ("/health", "/health/qdrant", "/health/all"):
        try:
            outputs.append(_fetch_json(f"{api_url}{endpoint}", evidence_dir / f"production{endpoint.replace('/', '_')}.json"))
        except (URLError, TimeoutError, OSError) as exc:
            errors.append({"endpoint": endpoint, "error": str(exc)})

    qdrant_payloads = [item["payload"] for item in outputs if "qdrant" in item["url"] or "health" in item["url"]]
    vector_count = None
    ready = False
    for payload in qdrant_payloads:
        candidates = [payload]
        if isinstance(payload, dict):
            candidates.extend(v for v in payload.values() if isinstance(v, dict))
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            if candidate.get("ready") is True or str(candidate.get("status", "")).lower() in {"healthy", "ready"}:
                ready = True
            for key in ("vector_count", "vectors", "points_count", "indexed_vectors"):
                if isinstance(candidate.get(key), int):
                    vector_count = candidate[key]
    status = "PASS" if outputs and not errors and ready and (vector_count or 0) > 0 else "FAIL"
    return _gate(
        status,
        "production_qdrant_baseline",
        outputs=[{"url": item["url"], "output": item["output"]} for item in outputs],
        errors=errors,
        ready=ready,
        vector_count=vector_count,
    )


def load_gate(evidence_dir: Path, run_cluster_load: bool) -> dict:
    if not run_cluster_load:
        return _gate(
            "BLOCKED",
            "sovereign_cluster_1000_user_load",
            missing=["explicit --run-cluster-load flag"],
            run_when_ready=(
                "KUBECONFIG=/path/to/sovereign-cluster "
                "python scripts/run_final_external_gates.py --run-cluster-load"
            ),
        )

    missing_tools = [tool for tool in ("kubectl", "docker") if shutil.which(tool) is None]
    if missing_tools:
        return _gate("BLOCKED", "sovereign_cluster_1000_user_load", missing=[f"tool:{tool}" for tool in missing_tools])

    context_blocker = _cluster_context_preflight(evidence_dir)
    if context_blocker is not None:
        return context_blocker

    cluster = _run(["kubectl", "cluster-info"], timeout=30, output=evidence_dir / "kubectl_cluster_info.log")
    if cluster["exit_code"] != 0:
        return _gate(
            "BLOCKED",
            "sovereign_cluster_1000_user_load",
            missing=["reachable Kubernetes cluster"],
            result=cluster,
        )

    result = _run(
        ["bash", "tests/load/run-locust-k8s.sh", "production"],
        timeout=2400,
        output=evidence_dir / "c4_1000_user_locust.log",
    )
    return _gate(
        "PASS" if result["exit_code"] == 0 else "FAIL",
        "sovereign_cluster_1000_user_load",
        result=result,
    )


def signing_gate(evidence_dir: Path) -> dict:
    signature_dir = REPO_ROOT / "docs/handover/signatures"
    signature_dir.mkdir(parents=True, exist_ok=True)

    missing_docs = [str(path.relative_to(REPO_ROOT)) for path in HANDOVER_DOCS if not path.exists()]
    digest_lines = []
    for path in HANDOVER_DOCS:
        if not path.exists():
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        digest_lines.append(f"{digest}  {path.relative_to(REPO_ROOT)}")
    digest_path = evidence_dir / "handover_sha256_manifest.txt"
    digest_path.write_text("\n".join(digest_lines) + "\n")

    secret_keys = _run(
        ["gpg", "--list-secret-keys", "--keyid-format", "LONG"],
        timeout=30,
        output=evidence_dir / "gpg_secret_key_check.log",
    )
    signatures = sorted(signature_dir.glob("*.asc"))
    verify_results = []
    for sig in signatures:
        doc = signature_dir.parent / sig.name.removesuffix(".asc")
        verify_results.append(
            _run(["gpg", "--verify", str(sig), str(doc)], timeout=30, output=evidence_dir / f"verify_{sig.name}.log")
        )

    status = "PASS" if not missing_docs and len(signatures) >= 8 and all(item["exit_code"] == 0 for item in verify_results) else "BLOCKED"
    missing = []
    if missing_docs:
        missing.extend(missing_docs)
    if len(signatures) < 8:
        missing.append(f"8 verified .asc signatures required, found {len(signatures)}")
    if secret_keys["exit_code"] != 0 or not (evidence_dir / "gpg_secret_key_check.log").read_text().strip():
        missing.append("founder private GPG key on signing machine")

    return _gate(
        status,
        "founder_gpg_signing",
        missing=missing,
        digest_manifest=str(digest_path),
        secret_key_check=secret_keys,
        signatures_found=len(signatures),
        verification_results=verify_results,
        run_when_ready=(
            "cd docs/handover/signatures && "
            "for doc in ../README.md ../SYSTEM_OVERVIEW.md ../ARCHITECTURE.md ../API_REFERENCE.md "
            "../OPERATIONS_RUNBOOK.md ../SECURITY_COMPLIANCE_ATTESTATION.md ../DATA_INTAKE_PROTOCOL.md "
            "../UAT_RESULTS.md; do gpg --armor --detach-sign --output \"$(basename \"$doc\").asc\" \"$doc\"; done"
        ),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-dir", default=str(DEFAULT_EVIDENCE_DIR))
    parser.add_argument("--run-cluster-load", action="store_true")
    args = parser.parse_args()

    evidence_dir = Path(args.evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)

    report = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_head": _run(["git", "log", "-1", "--oneline"], output=evidence_dir / "git_head.log"),
        "env": {
            "NRG_DEPLOYED_FRONTEND_URL": _redacted_env("NRG_DEPLOYED_FRONTEND_URL"),
            "NRG_DEPLOYED_API_URL": _redacted_env("NRG_DEPLOYED_API_URL"),
            "NRG_PRODUCTION_API_URL": _redacted_env("NRG_PRODUCTION_API_URL"),
            "KUBECONFIG": _redacted_env("KUBECONFIG"),
        },
        "gates": [
            deployed_browser_gate(evidence_dir),
            qdrant_baseline_gate(evidence_dir),
            load_gate(evidence_dir, args.run_cluster_load),
            signing_gate(evidence_dir),
        ],
    }
    output = evidence_dir / "external_gate_status.json"
    output.write_text(json.dumps(report, indent=2))

    blocked_or_failed = [gate for gate in report["gates"] if gate["status"] != "PASS"]
    status = "PASS" if not blocked_or_failed else "BLOCKED"
    summary = evidence_dir / "EXTERNAL_GATE_SUMMARY.md"
    summary.write_text(
        "\n".join(
            [
                "# NRG External Final Gates",
                "",
                f"Generated: {report['generated_at']}",
                f"Overall status: **{status}**",
                "",
                "| Gate | Status | Missing / Notes |",
                "|---|---:|---|",
                *[
                    f"| {gate['gate']} | {gate['status']} | {', '.join(gate.get('missing', [])) or gate.get('evidence_dir', gate.get('run_when_ready', ''))} |"
                    for gate in report["gates"]
                ],
                "",
                "This file is a gate report, not a production readiness certificate.",
            ]
        )
        + "\n"
    )

    print(json.dumps({"status": status, "report": str(output), "summary": str(summary)}, indent=2))
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
