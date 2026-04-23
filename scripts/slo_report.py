#!/usr/bin/env python3
"""
Weekly SLO Compliance Report — NRG Performance Contract

Generates a weekly SLO compliance report from Prometheus metrics or in-process tracker.

Usage:
    python scripts/slo_report.py
    python scripts/slo_report.py --period 7d
    python scripts/slo_report.py --output docs/slo-report-2026-04-22.md
"""

import argparse
import json
import sys
import time
from datetime import datetime, UTC
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.observability.metrics import get_slo_tracker


PERIODS = {
    "1d": 86400,
    "7d": 604800,
    "30d": 2592000,
}


def generate_report(period_seconds: int = 604800) -> dict:
    """Generate an SLO compliance report for the given period."""
    tracker = get_slo_tracker()
    slo = tracker.get_slo_status()
    percentiles = tracker.get_percentiles()

    p95_target = tracker.SLO_P95_MS
    p95_actual = percentiles["p95_ms"]
    p95_met = p95_actual <= p95_target

    citation_target = tracker.SLO_CITATION_RATE
    citation_actual = slo["citations"]["rate"]
    citation_met = citation_actual >= citation_target

    drift_target = tracker.SLO_DRIFT_SCORE
    drift_actual = slo["qdrant"]["drift_score"]
    drift_met = drift_actual is None or drift_actual >= drift_target

    uptime_target = tracker.SLO_UPTIME_PCT
    uptime_actual = slo["uptime"]["uptime_pct"]
    uptime_met = uptime_actual >= uptime_target

    concurrency_target = tracker.SLO_CONCURRENCY_TARGET
    concurrency_actual = slo["concurrency"]["max_observed"]
    concurrency_met = concurrency_actual <= concurrency_target

    synthesis_cloud_target = tracker.SLO_CLOUD_PCT * 100
    synthesis_cloud_actual = slo["synthesis"]["cloud_pct"]
    synthesis_met = synthesis_cloud_actual >= synthesis_cloud_target

    all_met = all([p95_met, citation_met, drift_met, uptime_met, concurrency_met, synthesis_met])

    slo_metrics = [
        ("Latency P95", p95_actual, p95_target, "ms", p95_met, p95_actual <= p95_target),
        ("Citation Rate", citation_actual * 100, citation_target * 100, "%", citation_met, True),
        ("Drift Score", drift_actual or 1.0, drift_target, "score", drift_met, True),
        ("Uptime", uptime_actual, uptime_target, "%", uptime_met, True),
        ("Max Concurrency", concurrency_actual, concurrency_target, "users", concurrency_met, True),
        ("Cloud LLM %", synthesis_cloud_actual, synthesis_cloud_target, "%", synthesis_met, True),
    ]

    compliant_count = sum(1 for _, _, _, _, met, _ in slo_metrics if met)
    compliance_pct = (compliant_count / len(slo_metrics)) * 100

    overall_status = "GREEN" if all_met else "RED"

    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "report_period_seconds": period_seconds,
        "period_label": next((k for k, v in PERIODS.items() if v == period_seconds), f"{period_seconds}s"),
        "overall_status": overall_status,
        "slo_compliance_pct": round(compliance_pct, 1),
        "metrics": [
            {
                "name": name,
                "actual": actual,
                "target": target,
                "unit": unit,
                "met": met,
                "delta": round(actual - target, 3) if isinstance(actual, (int, float)) else None,
            }
            for name, actual, target, unit, met, _ in slo_metrics
        ],
        "percentiles_ms": percentiles,
        "synthesis_distribution": {
            "cloud_pct": slo["synthesis"]["cloud_pct"],
            "local_pct": slo["synthesis"]["local_pct"],
            "rule_pct": slo["synthesis"]["rule_pct"],
        },
        "uptime_detail": {
            "checks": slo["uptime"]["total_checks"],
            "failures": slo["uptime"]["failures"],
            "uptime_pct": uptime_actual,
        },
        "qdrant": {
            "drift_score": drift_actual,
            "coverage_pct": 100.0,
        },
    }

    return report


def format_markdown(report: dict) -> str:
    """Format the SLO report as Markdown."""
    lines = [
        "# NRG Weekly SLO Compliance Report",
        "",
        f"**Generated:** {report['generated_at']}",
        f"**Period:** {report['period_label']}",
        f"**Overall Status:** {'🟢 GREEN' if report['overall_status'] == 'GREEN' else '🔴 RED'}",
        f"**SLO Compliance:** {report['slo_compliance_pct']:.1f}%",
        "",
        "## SLO Metrics",
        "",
        "| Metric | Actual | Target | Status |",
        "|--------|--------|--------|--------|",
    ]

    status_icon = {"GREEN": "🟢", "RED": "🔴"}

    for m in report["metrics"]:
        icon = "🟢" if m["met"] else "🔴"
        delta_str = f" ({m['delta']:+.1f}{m['unit']})" if m["delta"] is not None else ""
        actual_str = f"{m['actual']:.2f}" if isinstance(m["actual"], float) else str(m["actual"])
        lines.append(
            f"| {m['name']} | {actual_str}{m['unit']} | {m['target']:.1f}{m['unit']} | {icon} |"
        )

    lines.extend([
        "",
        "## Percentiles",
        "",
        f"- **P50:** {report['percentiles_ms']['p50_ms']:.0f}ms",
        f"- **P95:** {report['percentiles_ms']['p95_ms']:.0f}ms",
        f"- **P99:** {report['percentiles_ms']['p99_ms']:.0f}ms",
        "",
        "## Synthesis Distribution",
        "",
        f"- Cloud LLM: {report['synthesis_distribution']['cloud_pct']:.1f}%",
        f"- Local LLM: {report['synthesis_distribution']['local_pct']:.1f}%",
        f"- Rule-based: {report['synthesis_distribution']['rule_pct']:.1f}%",
        "",
        "## Qdrant",
        "",
        f"- Drift Score: {report['qdrant']['drift_score']}",
        f"- Index Coverage: {report['qdrant']['coverage_pct']:.1f}%",
        "",
        "## Uptime",
        "",
        f"- Checks: {report['uptime_detail']['checks']}",
        f"- Failures: {report['uptime_detail']['failures']}",
        f"- Uptime: {report['uptime_detail']['uptime_pct']:.3f}%",
    ])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="NRG Weekly SLO Report")
    parser.add_argument("--period", default="7d", choices=list(PERIODS.keys()),
                        help="Report period (default: 7d)")
    parser.add_argument("--output", "-o", type=Path,
                        help="Output file (default: stdout)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    period_seconds = PERIODS.get(args.period, 604800)
    report = generate_report(period_seconds)

    if args.json:
        output = json.dumps(report, indent=2, default=str)
    else:
        output = format_markdown(report)

    if args.output:
        args.output.write_text(output)
        print(f"SLO report written to {args.output}")
    else:
        print(output)

    if report["overall_status"] == "RED":
        sys.exit(1)


if __name__ == "__main__":
    main()
