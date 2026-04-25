#!/usr/bin/env python3
"""
Chain Seal Attestation — C1/C2/C6 Live Verification.

Runs the 3 hard constraints on sovereign cluster:
  C1: PII compliance (no raw PII in API responses)
  C2: Per-user audit binding (every query bound to user identity)
  C6: Egress allowlist (no unauthorized data egress)

Usage:
    # Local (against running API):
    python scripts/chain_seal_attestation.py --mode local

    # Sovereign cluster:
    python scripts/chain_seal_attestation.py --mode sovereign --namespace nrg

    # Dry run (show commands only):
    python scripts/chain_seal_attestation.py --dry-run

Output:
    evidence/05_chain_seal.json   — structured attestation
    evidence/05_chain_seal.md     — human-readable attestation
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime, UTC
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "evidence"


@dataclass
class TestResult:
    name: str
    passed: bool
    duration_sec: float
    output: str
    errors: list[str]


def run_pytest(
    test_path: str,
    verbose: bool = True,
    timeout: int = 120,
) -> TestResult:
    """Run pytest for a given test path."""
    start = time.time()
    cmd = [
        sys.executable, "-m", "pytest",
        test_path,
        "-v", "--tb=short",
        "-q",
    ]
    print(f"\n  $ {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=str(ROOT),
    )
    duration = time.time() - start
    passed = result.returncode == 0
    output = (result.stdout + result.stderr)[-3000:]

    errors = []
    if not passed:
        for line in output.split("\n"):
            if "FAILED" in line or "ERROR" in line or "AssertionError" in line:
                errors.append(line.strip())

    return TestResult(
        name=test_path,
        passed=passed,
        duration_sec=round(duration, 1),
        output=output[-1000:],
        errors=errors[:5],
    )


def verify_chain() -> TestResult:
    """Run audit chain verification."""
    start = time.time()
    try:
        from src.audit import verify_chain as vc
        valid, errs, count = vc()
        duration = time.time() - start
        passed = valid and len(errs) == 0
        output = f"Valid: {valid}, Events: {count}, Errors: {errs}"
        return TestResult(
            name="audit/verify_chain",
            passed=passed,
            duration_sec=round(duration, 1),
            output=output,
            errors=errs if errs else [],
        )
    except Exception as e:
        return TestResult(
            name="audit/verify_chain",
            passed=False,
            duration_sec=time.time() - start,
            output=str(e),
            errors=[str(e)],
        )


def run_local_attestation() -> dict:
    """Run all attestation checks locally."""
    print("\n" + "=" * 60)
    print("CHAIN SEAL ATTESTATION — Local Mode")
    print("=" * 60)

    results: list[TestResult] = []

    # C1: PII Compliance
    print("\n[C1] PII Compliance Tests...")
    r = run_pytest("tests/security/test_pii_indian.py")
    r.name = "C1: PII Compliance"
    results.append(r)
    print(f"  {'✅ PASS' if r.passed else '❌ FAIL'} ({r.duration_sec}s)")

    # C2: Per-user audit binding
    print("\n[C2] Per-User Audit Binding...")
    r = run_pytest("tests/security/test_per_user_audit_binding.py")
    r.name = "C2: Per-User Audit Binding"
    results.append(r)
    print(f"  {'✅ PASS' if r.passed else '❌ FAIL'} ({r.duration_sec}s)")

    # C6: Egress allowlist
    print("\n[C6] Egress Allowlist...")
    r = run_pytest("tests/security/test_egress_allowlist.py")
    r.name = "C6: Egress Allowlist"
    results.append(r)
    print(f"  {'✅ PASS' if r.passed else '❌ FAIL'} ({r.duration_sec}s)")

    # Chain integrity
    print("\n[Chain] Audit Chain Verification...")
    r = verify_chain()
    r.name = "Audit Chain Integrity"
    results.append(r)
    print(f"  {'✅ PASS' if r.passed else '❌ FAIL'} ({r.duration_sec}s)")

    return package_results(results)


def run_sovereign_attestation(namespace: str = "nrg") -> dict:
    """Run attestation via kubectl exec on sovereign cluster."""
    print("\n" + "=" * 60)
    print(f"CHAIN SEAL ATTESTATION — Sovereign Mode (namespace={namespace})")
    print("=" * 60)

    results: list[TestResult] = []

    tests = [
        ("C1: PII Compliance", "tests/security/test_pii_indian.py"),
        ("C2: Per-User Audit Binding", "tests/security/test_per_user_audit_binding.py"),
        ("C6: Egress Allowlist", "tests/security/test_egress_allowlist.py"),
    ]

    for label, path in tests:
        print(f"\n[{label}]...")
        cmd = [
            "kubectl", "-n", namespace, "exec", "deploy/api", "--",
            sys.executable, "-m", "pytest", path, "-v", "--tb=short", "-q",
        ]
        print(f"  $ {' '.join(cmd)}")
        start = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        duration = time.time() - start
        passed = result.returncode == 0
        output = (result.stdout + result.stderr)[-2000:]
        errors = []
        if not passed:
            for line in output.split("\n"):
                if "FAILED" in line or "AssertionError" in line:
                    errors.append(line.strip())
        r = TestResult(name=label, passed=passed, duration_sec=round(duration, 1), output=output, errors=errors[:5])
        results.append(r)
        print(f"  {'✅ PASS' if r.passed else '❌ FAIL'} ({r.duration_sec}s)")

    # Chain verification
    print("\n[Chain] Audit Chain...")
    cmd = [
        "kubectl", "-n", namespace, "exec", "deploy/api", "--",
        sys.executable, "-c",
        "from src.audit import verify_chain; v,e,n=verify_chain(); print(f'Valid={v} Events={n} Errors={e}')"
    ]
    print(f"  $ {' '.join(cmd)}")
    start = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    duration = time.time() - start
    valid = result.returncode == 0 and "Valid=True" in result.stdout
    output = (result.stdout + result.stderr).strip()
    errors = [] if valid else [output]
    r = TestResult(name="Audit Chain Integrity", passed=valid, duration_sec=round(duration, 1), output=output, errors=errors)
    results.append(r)
    print(f"  {'✅ PASS' if r.passed else '❌ FAIL'} ({r.duration_sec}s)")

    return package_results(results)


def package_results(results: list[TestResult]) -> dict:
    """Package all test results into attestation output."""
    now = datetime.now(UTC).isoformat()
    passed_all = all(r.passed for r in results)
    total_duration = sum(r.duration_sec for r in results)

    attestation = {
        "timestamp": now,
        "status": "PASS" if passed_all else "FAIL",
        "total_duration_sec": round(total_duration, 1),
        "constraints": {},
    }

    for r in results:
        attestation["constraints"][r.name] = {
            "passed": r.passed,
            "duration_sec": r.duration_sec,
            "errors": r.errors,
        }

    # Write JSON
    json_path = EVIDENCE_DIR / "05_chain_seal.json"
    json_path.write_text(json.dumps(attestation, indent=2))
    print(f"\n  JSON: {json_path}")

    # Write Markdown
    md_lines = [
        "# Chain Seal Attestation — C1/C2/C6 + Audit Chain",
        "",
        f"**Generated:** {now}",
        f"**Status:** {'✅ ALL PASSED' if passed_all else '❌ FAILURES DETECTED'}",
        "",
        "## Constraint Results",
        "",
        "| Constraint | Test | Duration | Status |",
        "|------------|------|----------|--------|",
    ]

    constraint_names = {
        "C1: PII Compliance": "C1: Raw PII never in API responses",
        "C2: Per-User Audit Binding": "C2: Every query bound to user identity",
        "C6: Egress Allowlist": "C6: No unauthorized data egress",
        "Audit Chain Integrity": "Audit chain HMAC verified",
    }

    for r in results:
        label = constraint_names.get(r.name, r.name)
        icon = "✅" if r.passed else "❌"
        md_lines.append(f"| {label} | {r.name} | {r.duration_sec}s | {icon} |")

    md_lines += [
        "",
        "## Detailed Results",
        "",
    ]

    for r in results:
        icon = "✅" if r.passed else "❌"
        md_lines.append(f"### {icon} {r.name}")
        if r.errors:
            md_lines.append(f"- Errors: `{'` | `'.join(r.errors)}`")
        md_lines.append(f"- Duration: {r.duration_sec}s")
        md_lines.append("")

    md_lines.append(f"\n> **Attestation:** Generated by `scripts/chain_seal_attestation.py` at {now} UTC")

    md_path = EVIDENCE_DIR / "05_chain_seal.md"
    md_path.write_text("\n".join(md_lines))
    print(f"  MD: {md_path}")

    print(f"\n{'='*60}")
    print(f"CHAIN SEAL: {'✅ PASSED — All constraints verified' if passed_all else '❌ FAILED — See errors above'}")
    print(f"{'='*60}")

    return attestation


def main():
    parser = argparse.ArgumentParser(description="NRG Chain Seal Attestation")
    parser.add_argument("--mode", choices=["local", "sovereign"], default="local")
    parser.add_argument("--namespace", default="nrg", help="Kubernetes namespace (sovereign mode)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.dry_run:
        print("[DRY RUN] Commands that would run:")
        print("  # C1:", "pytest tests/security/test_pii_indian.py -v")
        print("  # C2:", "pytest tests/security/test_per_user_audit_binding.py -v")
        print("  # C6:", "pytest tests/security/test_egress_allowlist.py -v")
        print("  # Chain: from src.audit import verify_chain; verify_chain()")
        return

    if args.mode == "local":
        result = run_local_attestation()
        sys.exit(0 if result["status"] == "PASS" else 1)
    else:
        result = run_sovereign_attestation(args.namespace)
        sys.exit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
