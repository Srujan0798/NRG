#!/usr/bin/env python3
"""Generate the NRG seven-pillar data quality scorecard."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.observability.data_quality import (  # noqa: E402
    DEFAULT_CORE_TABLES,
    DataQualityScorecard,
    DataQualityThresholds,
    load_expected_tables,
    run_data_quality_scorecard,
)

DEFAULT_DATABASE_URL = "sqlite:///nrg_research.db"
DEFAULT_JSON_OUTPUT = Path("docs/ops/data_quality_scorecard.json")
DEFAULT_MARKDOWN_OUTPUT = Path("docs/ops/data_quality_scorecard.md")
# Freshness score decays continuously as local fixtures age, so the baseline gate
# treats sub-0.5 percentage-point score differences as noise and still catches
# material quality regressions or any P0 alert.
BASELINE_SCORE_EPSILON = 0.005


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    database_url = args.database_url or os.getenv("DATABASE_URL") or DEFAULT_DATABASE_URL
    if _is_missing_sqlite_file(database_url):
        message = f"Data quality database not found for URL: {database_url}"
        if args.require_db:
            parser.error(message)
        print(json.dumps({"ok": True, "skipped": True, "reason": message}))
        return 0

    thresholds = DataQualityThresholds(
        expected_table_count=args.expected_table_count,
        referential_integrity_min=args.referential_integrity_min,
        referential_integrity_p0=args.referential_integrity_p0,
        max_null_rate=args.max_null_rate,
        max_freshness_days=args.max_freshness_days,
        min_core_rows=args.min_core_rows,
        pii_sample_limit=args.pii_sample_limit,
    )
    expected_tables = load_expected_tables() or None
    core_tables = DEFAULT_CORE_TABLES if not args.core_table else set(args.core_table)
    non_pii_tables = set(args.non_pii_table) if args.non_pii_table else None

    scorecard = run_data_quality_scorecard(
        database_url=database_url,
        json_output=args.json_output,
        markdown_output=args.markdown_output,
        expected_tables=expected_tables,
        core_tables=core_tables,
        non_pii_tables=non_pii_tables,
        thresholds=thresholds,
    )

    if args.print_json:
        print(scorecard.to_json(), end="")
    else:
        print(
            f"ok: {str(scorecard.ok).lower()} "
            f"status: {scorecard.overall_status} "
            f"score: {scorecard.overall_score:.3f} "
            f"alerts: {len(scorecard.alerts)}"
        )

    if args.check_baseline and args.baseline:
        baseline = _load_baseline(args.baseline)
        if baseline and _score_dropped(scorecard, baseline):
            baseline_score = float(baseline.get("overall_score", 0.0))
            print(
                "Data quality scorecard dropped below baseline "
                f"({scorecard.overall_score:.3f} < {baseline_score:.3f})",
                file=sys.stderr,
            )
            return 1

    if args.fail_on_p0 and any(alert.severity == "P0" for alert in scorecard.alerts):
        print("Data quality scorecard contains P0 alerts", file=sys.stderr)
        return 1
    if args.fail_on_fail and not scorecard.ok:
        print("Data quality scorecard failed one or more pillars", file=sys.stderr)
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", help="SQLAlchemy database URL. Defaults to DATABASE_URL or local SQLite.")
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT)
    parser.add_argument("--baseline", type=Path, help="Existing JSON scorecard used as a no-regression baseline.")
    parser.add_argument("--check-baseline", action="store_true", help="Fail if the score drops below --baseline.")
    parser.add_argument("--fail-on-p0", action="store_true", help="Return non-zero when a P0 alert is present.")
    parser.add_argument("--fail-on-fail", action="store_true", help="Return non-zero when any pillar fails.")
    parser.add_argument("--require-db", action="store_true", help="Fail instead of skipping when local SQLite is missing.")
    parser.add_argument("--print-json", action="store_true", help="Print the full scorecard JSON to stdout.")
    parser.add_argument("--expected-table-count", type=int, default=58)
    parser.add_argument("--referential-integrity-min", type=float, default=0.99)
    parser.add_argument("--referential-integrity-p0", type=float, default=0.90)
    parser.add_argument("--max-null-rate", type=float, default=0.05)
    parser.add_argument("--max-freshness-days", type=int, default=7)
    parser.add_argument("--min-core-rows", type=int, default=1000)
    parser.add_argument("--pii-sample-limit", type=int, default=1000)
    parser.add_argument("--core-table", action="append", default=[], help="Core table override; repeatable.")
    parser.add_argument("--non-pii-table", action="append", default=[], help="Non-PII table override; repeatable.")
    return parser


def _load_baseline(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text())


def _score_dropped(scorecard: DataQualityScorecard, baseline: dict[str, object]) -> bool:
    baseline_score = float(baseline.get("overall_score", 0.0))
    if scorecard.overall_score + BASELINE_SCORE_EPSILON < baseline_score:
        return True
    baseline_pillars = baseline.get("pillars", {})
    current_pillars = scorecard.to_dict().get("pillars", {})
    if not isinstance(baseline_pillars, dict):
        return False
    for pillar_name, baseline_result in baseline_pillars.items():
        if not isinstance(baseline_result, dict):
            continue
        current_result = current_pillars.get(pillar_name)
        if not current_result:
            return True
        current_score = float(current_result.get("score", 0.0))
        baseline_pillar_score = float(baseline_result.get("score", 0.0))
        if current_score + BASELINE_SCORE_EPSILON < baseline_pillar_score:
            return True
    return False


def _is_missing_sqlite_file(database_url: str) -> bool:
    if not database_url.startswith("sqlite:///"):
        return False
    path = Path(database_url.removeprefix("sqlite:///"))
    if str(path) in {":memory:", ""}:
        return False
    if not path.is_absolute():
        path = REPO_ROOT / path
    return not path.exists()


if __name__ == "__main__":
    raise SystemExit(main())
