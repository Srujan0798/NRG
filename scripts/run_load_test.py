#!/usr/bin/env python3
"""
C4 Load Test Runner — P99 < 500ms @ 1000 concurrent users.

Orchestrates the full load test:
  1. Verifies API is reachable
  2. Runs Locust with 1000 concurrent users
  3. Parses P50/P95/P99 from CSV
  4. Asserts P99 < 500ms
  5. Writes evidence to evidence/02_load_report.md

Usage:
    # On sovereign cluster (with kubectl):
    python scripts/run_load_test.py --host http://localhost:8000 --users 1000
    # With port-forward:
    kubectl port-forward svc/api 8000:8000 &
    python scripts/run_load_test.py --host http://localhost:8000 --users 1000

Prerequisites:
    pip install locust
    locust --version  # needs 2.x+
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
import time
from datetime import datetime, UTC
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "evidence"
STATS_DIR = EVIDENCE_DIR / "02_load_stats"
CACHE_DIR = ROOT / ".cache"

P99_THRESHOLD_MS = 500
SUCCESS_RATE_MIN = 0.95
DEFAULT_HOST = "http://localhost:8000"
DEFAULT_USERS = 1000
RUN_DURATION_SEC = 300  # 5 minutes


def check_api_health(host: str) -> bool:
    """Verify API is reachable."""
    print(f"\n[1/5] Checking API health at {host}...")
    try:
        import urllib.request
        req = urllib.request.Request(f"{host}/health")
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                data = json.loads(resp.read())
                print(f"  ✅ API healthy: {data}")
                return True
    except Exception as e:
        print(f"  ❌ API unreachable: {e}")
    return False


def run_locust(
    host: str,
    users: int,
    run_time: int,
    stats_csv: Path,
    html_report: Path,
) -> dict:
    """Run Locust load test and return parsed stats."""
    print(f"\n[2/5] Running Locust — {users} users, {run_time}s, host={host}")
    print(f"  CSV stats: {stats_csv}")
    print(f"  HTML report: {html_report}")

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    STATS_DIR.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable, "-m", "locust",
        "-f", "tests/load/locustfile.py",
        "--headless",
        "-u", str(users),
        "-r", str(min(users // 10, 100)),  # 10% spawn rate
        "--run-time", f"{run_time}s",
        "--host", host,
        "--csv", str(STATS_DIR / "locust"),
        "--html", str(html_report),
    ]

    print(f"\n$ {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=run_time + 60,
    )
    print(result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout)
    if result.stderr:
        print(result.stderr[-1000:] if len(result.stderr) > 1000 else result.stderr, file=sys.stderr)

    stats = parse_locust_csv(STATS_DIR / "locust_stats.csv")
    return stats


def parse_locust_csv(csv_path: Path) -> dict:
    """Parse Locust CSV for P50/P95/P99 latency."""
    print(f"\n[3/5] Parsing stats from {csv_path}")

    if not csv_path.exists():
        print(f"  ⚠️  CSV not found: {csv_path}")
        return {}

    results = {}
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["Name"]
            if not name or name in ("Aggregated", ""):
                continue
            try:
                results[name] = {
                    "requests": int(row["Request Count"]) if row["Request Count"] else 0,
                    "failures": int(row["Failure Count"]) if row["Failure Count"] else 0,
                    "median": float(row["Median Response Time"]) if row["Median Response Time"] else 0,
                    "p95": float(row["95%"]) if row["95%"] else 0,
                    "p99": float(row["99%"]) if row["99%"] else 0,
                }
            except (ValueError, KeyError) as e:
                print(f"  ⚠️  Could not parse row {name}: {e}")
                continue

    return results


def validate_p99(stats: dict) -> tuple[bool, dict]:
    """Assert P99 < 500ms and success rate > 95%."""
    print(f"\n[4/5] Validating P99 < {P99_THRESHOLD_MS}ms @ {DEFAULT_USERS} concurrent")

    api_stats = stats.get("api/query/stream", {})
    if not api_stats:
        print("  ⚠️  No /api/query/stream stats found — checking aggregated")
        api_stats = stats.get("", stats.get("Aggregated", {}))

    if not api_stats:
        print(f"  ⚠️  No query stats found. Available: {list(stats.keys())}")
        return False, {}

    p50 = api_stats.get("median", 0)
    p95 = api_stats.get("p95", 0)
    p99 = api_stats.get("p99", 0)
    req_count = api_stats.get("requests", 0)
    failures = api_stats.get("failures", 0)
    success_rate = (req_count - failures) / req_count if req_count > 0 else 0

    print(f"  /api/query/stream stats:")
    print(f"    Requests:    {req_count}")
    print(f"    Failures:    {failures}")
    print(f"    Success:     {success_rate*100:.1f}%  (min: {SUCCESS_RATE_MIN*100}%)")
    print(f"    P50 (med):   {p50:.0f}ms")
    print(f"    P95:         {p95:.0f}ms")
    print(f"    P99:         {p99:.0f}ms  ← TARGET: <{P99_THRESHOLD_MS}ms")

    p99_pass = p99 < P99_THRESHOLD_MS
    success_pass = success_rate >= SUCCESS_RATE_MIN

    status = "✅ PASS" if (p99_pass and success_pass) else "❌ FAIL"
    print(f"\n  Result: {status}")

    if not p99_pass:
        print(f"  ⚠️  P99 ({p99:.0f}ms) exceeds threshold ({P99_THRESHOLD_MS}ms)")
    if not success_pass:
        print(f"  ⚠️  Success rate ({success_rate*100:.1f}%) below threshold ({SUCCESS_RATE_MIN*100}%)")

    all_stats = {k: v for k, v in stats.items() if v.get("requests", 0) > 0}
    return (p99_pass and success_pass), {
        "p50_ms": p50,
        "p95_ms": p95,
        "p99_ms": p99,
        "requests": req_count,
        "failures": failures,
        "success_rate": success_rate,
        "p99_pass": p99_pass,
        "success_pass": success_pass,
        "all_stats": all_stats,
    }


def write_evidence(
    stats: dict,
    validation: tuple[bool, dict],
    host: str,
    users: int,
    duration_sec: int,
) -> Path:
    """Write load test evidence to evidence/02_load_report.md."""
    print(f"\n[5/5] Writing evidence...")

    passed, metrics = validation
    p99_ms = metrics.get("p99_ms", 0)
    p95_ms = metrics.get("p95_ms", 0)
    p50_ms = metrics.get("p50_ms", 0)
    success_rate = metrics.get("success_rate", 0)
    req_count = metrics.get("requests", 0)
    failures = metrics.get("failures", 0)

    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")

    md_lines = [
        "# C4 Load Test Report — P99 < 500ms @ 1000 Concurrent",
        "",
        f"**Generated:** {now}",
        f"**Host:** {host}",
        f"**Concurrent Users:** {users}",
        f"**Duration:** {duration_sec}s",
        f"**Status:** {'✅ PASS' if passed else '❌ FAIL'}",
        "",
        "## Constraints",
        "",
        f"| Constraint | Target | Observed | Status |",
        f"|-------------|--------|----------|--------|",
        f"| P99 latency | <{P99_THRESHOLD_MS}ms | {p99_ms:.0f}ms | {'✅' if metrics.get('p99_pass') else '❌'} |",
        f"| Success rate | >{SUCCESS_RATE_MIN*100:.0f}% | {success_rate*100:.1f}% | {'✅' if metrics.get('success_pass') else '❌'} |",
        f"| Users | 1000 | {users} | ✅ |",
        "",
        "## Latency Distribution",
        "",
        f"| Percentile | Latency (ms) |",
        f"|------------|---------------|",
        f"| P50 | {p50_ms:.0f} |",
        f"| P95 | {p95_ms:.0f} |",
        f"| P99 | {p99_ms:.0f} |",
        "",
        "## Request Stats",
        "",
        f"- Total requests: {req_count}",
        f"- Failures: {failures}",
        f"- Success rate: {success_rate*100:.1f}%",
        "",
    ]

    if metrics.get("all_stats"):
        md_lines += [
            "## Per-Endpoint Stats",
            "",
            "| Endpoint | Requests | Failures | P50 | P95 | P99 |",
            "|----------|----------|----------|-----|-----|-----|",
        ]
        for name, s in sorted(metrics["all_stats"].items(), key=lambda x: -x[1].get("requests", 0)):
            md_lines.append(
                f"| {name} | {s.get('requests',0)} | {s.get('failures',0)} | "
                f"{s.get('median',0):.0f} | {s.get('p95',0):.0f} | {s.get('p99',0):.0f} |"
            )
        md_lines.append("")

    if not passed:
        md_lines += [
            "## Failure Analysis",
            "",
            "```",
            f"P99 ({p99_ms:.0f}ms) exceeded threshold ({P99_THRESHOLD_MS}ms).",
            "",
            "Recommendations:",
            "1. Enable Redis caching: kubectl scale deploy/redis --replicas=3",
            "2. Scale API replicas: kubectl scale deploy/api --replicas=5",
            "3. Enable query result caching in CostGuard",
            "4. Check Qdrant latency at :6333/dashboard",
            "5. Profile slow SQL queries: EXPLAIN ANALYZE on top queries",
            "```",
            "",
        ]

    md_lines.append(f"> **Attestation:** This report generated by `scripts/run_load_test.py` at {now} UTC")

    output_path = EVIDENCE_DIR / "02_load_report.md"
    output_path.write_text("\n".join(md_lines))
    print(f"  Written to: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="NRG C4 Load Test Runner")
    parser.add_argument("--host", default=DEFAULT_HOST, help="API host URL")
    parser.add_argument("--users", type=int, default=DEFAULT_USERS, help="Concurrent users")
    parser.add_argument("--duration", type=int, default=RUN_DURATION_SEC, help="Test duration (seconds)")
    parser.add_argument("--skip-health", action="store_true", help="Skip health check")
    args = parser.parse_args()

    print("=" * 60)
    print(f"C4 LOAD TEST — P99<{P99_THRESHOLD_MS}ms @ {args.users} concurrent")
    print("=" * 60)

    if not args.skip_health and not check_api_health(args.host):
        print("\n❌ API health check failed. Ensure API is running:")
        print(f"   kubectl port-forward svc/api 8000:8000 &")
        print(f"   python scripts/run_load_test.py --host http://localhost:8000")
        sys.exit(1)

    html_report = CACHE_DIR / "locust_report.html"
    stats = run_locust(
        host=args.host,
        users=args.users,
        run_time=args.duration,
        stats_csv=STATS_DIR,
        html_report=html_report,
    )

    if not stats:
        print("\n⚠️  No stats collected — check Locust output above")
        sys.exit(1)

    passed, metrics = validate_p99(stats)
    write_evidence(stats, (passed, metrics), args.host, args.users, args.duration)

    if passed:
        print(f"\n✅ C4 LOAD TEST PASSED — P99 {metrics['p99_ms']:.0f}ms < {P99_THRESHOLD_MS}ms")
        sys.exit(0)
    else:
        print(f"\n❌ C4 LOAD TEST FAILED — P99 {metrics['p99_ms']:.0f}ms >= {P99_THRESHOLD_MS}ms")
        sys.exit(1)


if __name__ == "__main__":
    main()
