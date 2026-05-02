#!/usr/bin/env python3
"""Validate NRG runtime image scan artifacts.

This script does not run Docker or Trivy. It reads already-captured JSON
artifacts and enforces the claim boundary used by the May 2 image-hardening
evidence:

- frontend runtime strict Trivy must have zero findings
- reverse-proxy nginx strict Trivy must have zero findings
- API runtime pip-audit must have zero vulnerable packages
- API runtime fixable HIGH/CRITICAL Trivy scan must have zero findings
- API runtime strict Trivy may still report unfixed Debian findings, but those
  are reported as a boundary and are not treated as a zero-CVE pass
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SEVERITIES = ("CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN")


@dataclass(frozen=True)
class TrivySummary:
    path: Path
    total: int
    by_severity: dict[str, int]
    fixable_by_severity: dict[str, int]

    @property
    def fixable_high_critical(self) -> int:
        return self.fixable_by_severity.get("CRITICAL", 0) + self.fixable_by_severity.get(
            "HIGH", 0
        )


@dataclass(frozen=True)
class PipAuditSummary:
    path: Path
    dependencies: int
    vulnerable_packages: int
    vulnerabilities: int


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text())
    except FileNotFoundError as exc:
        raise SystemExit(f"missing scan artifact: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid JSON artifact {path}: {exc}") from exc


def summarize_trivy(path: Path) -> TrivySummary:
    data = _load_json(path)
    counts = {severity: 0 for severity in SEVERITIES}
    fixable = {severity: 0 for severity in SEVERITIES}
    total = 0

    for result in data.get("Results") or []:
        for vuln in result.get("Vulnerabilities") or []:
            severity = vuln.get("Severity") or "UNKNOWN"
            if severity not in counts:
                severity = "UNKNOWN"
            total += 1
            counts[severity] += 1
            if vuln.get("FixedVersion"):
                fixable[severity] += 1

    return TrivySummary(path=path, total=total, by_severity=counts, fixable_by_severity=fixable)


def summarize_pip_audit(path: Path) -> PipAuditSummary:
    data = _load_json(path)
    dependencies = data.get("dependencies") or []
    vulnerable_packages = 0
    vulnerabilities = 0

    for dependency in dependencies:
        vulns = dependency.get("vulns") or []
        if vulns:
            vulnerable_packages += 1
            vulnerabilities += len(vulns)

    return PipAuditSummary(
        path=path,
        dependencies=len(dependencies),
        vulnerable_packages=vulnerable_packages,
        vulnerabilities=vulnerabilities,
    )


def _status(ok: bool) -> str:
    return "PASS" if ok else "FAIL"


def build_report(
    frontend: TrivySummary,
    nginx: TrivySummary,
    api_pip: PipAuditSummary,
    api_strict: TrivySummary,
    api_fixable: TrivySummary,
) -> tuple[str, bool]:
    rows: list[tuple[str, str, str]] = []
    failures: list[str] = []

    frontend_ok = frontend.total == 0
    nginx_ok = nginx.total == 0
    api_pip_ok = api_pip.vulnerabilities == 0
    api_fixable_ok = api_fixable.total == 0
    api_strict_no_critical = api_strict.by_severity.get("CRITICAL", 0) == 0

    if not frontend_ok:
        failures.append("frontend strict Trivy scan has findings")
    if not nginx_ok:
        failures.append("reverse-proxy strict Trivy scan has findings")
    if not api_pip_ok:
        failures.append("API pip-audit has vulnerable packages")
    if not api_fixable_ok:
        failures.append("API fixable HIGH/CRITICAL Trivy scan has findings")
    if not api_strict_no_critical:
        failures.append("API strict Trivy scan has CRITICAL findings")

    rows.append(
        (
            "Frontend runtime strict Trivy",
            _status(frontend_ok),
            f"total={frontend.total}",
        )
    )
    rows.append(("Reverse-proxy runtime strict Trivy", _status(nginx_ok), f"total={nginx.total}"))
    rows.append(
        (
            "API runtime pip-audit",
            _status(api_pip_ok),
            (
                f"dependencies={api_pip.dependencies}, "
                f"vulnerable_packages={api_pip.vulnerable_packages}, "
                f"vulnerabilities={api_pip.vulnerabilities}"
            ),
        )
    )
    rows.append(
        (
            "API runtime fixable HIGH/CRITICAL Trivy",
            _status(api_fixable_ok),
            f"total={api_fixable.total}",
        )
    )
    rows.append(
        (
            "API runtime strict Trivy boundary",
            "PARTIAL" if api_strict.total else "PASS",
            (
                f"total={api_strict.total}, "
                f"critical={api_strict.by_severity.get('CRITICAL', 0)}, "
                f"high={api_strict.by_severity.get('HIGH', 0)}, "
                f"fixable_high_critical={api_strict.fixable_high_critical}"
            ),
        )
    )

    report = [
        "# Runtime Image Scan Gate",
        "",
        "| Gate | Status | Detail |",
        "| --- | --- | --- |",
    ]
    report.extend(f"| {gate} | {status} | {detail} |" for gate, status, detail in rows)
    report.extend(
        [
            "",
            "## Claim Boundary",
            "",
            (
                "This gate passes only for local package scans, frontend/reverse-proxy strict "
                "OS scans, and API fixable HIGH/CRITICAL findings. It does not certify a "
                "zero-CVE API OS image when strict Trivy still reports unfixed vendor CVEs."
            ),
        ]
    )

    if failures:
        report.extend(["", "## Failures", ""])
        report.extend(f"- {failure}" for failure in failures)

    return "\n".join(report) + "\n", not failures


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frontend-trivy", required=True, type=Path)
    parser.add_argument("--nginx-trivy", required=True, type=Path)
    parser.add_argument("--api-pip-audit", required=True, type=Path)
    parser.add_argument("--api-trivy-strict", required=True, type=Path)
    parser.add_argument("--api-trivy-fixable", required=True, type=Path)
    parser.add_argument("--summary-out", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report, ok = build_report(
        frontend=summarize_trivy(args.frontend_trivy),
        nginx=summarize_trivy(args.nginx_trivy),
        api_pip=summarize_pip_audit(args.api_pip_audit),
        api_strict=summarize_trivy(args.api_trivy_strict),
        api_fixable=summarize_trivy(args.api_trivy_fixable),
    )

    if args.summary_out:
        args.summary_out.parent.mkdir(parents=True, exist_ok=True)
        args.summary_out.write_text(report)
    print(report, end="")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
