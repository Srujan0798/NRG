#!/usr/bin/env python3
"""Validate and document the 6-node orchestration pipeline contracts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.orchestration.contracts import (  # noqa: E402
    current_versions,
    detect_major_version_bumps,
    generate_contract_markdown,
    validate_contract_set,
)

DEFAULT_DOCS_OUTPUT = Path("docs/ops/pipeline_contracts.md")
DEFAULT_REPORT_OUTPUT = Path(".cache/pipeline_contracts_report.json")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    report = validate_contract_set()
    report["integration_required"] = False
    report["major_version_bumps"] = {}

    if args.version_baseline and args.version_baseline.exists():
        previous_versions = json.loads(args.version_baseline.read_text())
        if not isinstance(previous_versions, dict):
            parser.error("--version-baseline must be a JSON object of edge -> version")
        bumps = detect_major_version_bumps(previous_versions, current_versions())
        report["major_version_bumps"] = bumps
        report["integration_required"] = bool(bumps)

    if args.github_output:
        args.github_output.parent.mkdir(parents=True, exist_ok=True)
        args.github_output.write_text(
            f"integration_required={str(report['integration_required']).lower()}\n"
        )

    args.docs_output.parent.mkdir(parents=True, exist_ok=True)
    args.docs_output.write_text(generate_contract_markdown())

    args.report_output.parent.mkdir(parents=True, exist_ok=True)
    args.report_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    if args.print_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(
            f"ok: {str(report['ok']).lower()} "
            f"contracts: {len(report['contracts'])} "
            f"integration_required: {str(report['integration_required']).lower()}"
        )

    return 0 if report["ok"] else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docs-output", type=Path, default=DEFAULT_DOCS_OUTPUT)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT_OUTPUT)
    parser.add_argument(
        "--version-baseline",
        type=Path,
        help="Optional JSON file containing previous edge SemVer values.",
    )
    parser.add_argument(
        "--github-output",
        type=Path,
        help="Optional path to write GitHub Actions outputs.",
    )
    parser.add_argument("--print-json", action="store_true")
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
