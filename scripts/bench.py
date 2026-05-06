#!/usr/bin/env python3
"""Generate the weekly benchmark report used by the CI workflow."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.benchmark_queries import QueryBenchmark


def _noop_query() -> str:
    return "ok"


def main() -> int:
    benchmark = QueryBenchmark()
    stats = benchmark.benchmark_query(_noop_query, "noop_ci_benchmark", iterations=25)

    report_path = Path("docs/benchmarks/REPORT.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        "\n".join(
            [
                "# NRG Benchmark Report",
                "",
                f"Generated: {datetime.now(UTC).isoformat()}",
                "",
                "| Benchmark | Iterations | Mean ms | P95 ms | P99 ms |",
                "|---|---:|---:|---:|---:|",
                (
                    f"| {stats['query_name']} | {stats['iterations']} | "
                    f"{stats['mean_time_ms']:.3f} | {stats['p95_ms']:.3f} | {stats['p99_ms']:.3f} |"
                ),
                "",
            ]
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
