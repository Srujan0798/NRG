#!/usr/bin/env python3
"""
Benchmark utilities for query performance testing
"""

import logging
import time
import json
from typing import Dict, Any, List, Callable

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueryBenchmark:
    """Benchmark query performance"""

    def __init__(self):
        self.results = []

    def benchmark_query(
        self, query_func: Callable, query_name: str, iterations: int = 100
    ) -> Dict[str, Any]:
        """Benchmark a query function"""
        times = []

        logger.info(f"Benchmarking {query_name} ({iterations} iterations)")

        for i in range(iterations):
            start = time.time()
            result = query_func()
            elapsed = time.time() - start
            times.append(elapsed)

        # Calculate statistics
        times_sorted = sorted(times)

        stats = {
            "query_name": query_name,
            "iterations": iterations,
            "mean_time_ms": sum(times) / len(times) * 1000,
            "median_time_ms": times_sorted[len(times_sorted) // 2] * 1000,
            "p50_ms": times_sorted[int(len(times_sorted) * 0.50)] * 1000,
            "p95_ms": times_sorted[int(len(times_sorted) * 0.95)] * 1000,
            "p99_ms": times_sorted[int(len(times_sorted) * 0.99)] * 1000,
            "min_time_ms": min(times) * 1000,
            "max_time_ms": max(times) * 1000,
        }

        self.results.append(stats)

        logger.info(f"  Mean: {stats['mean_time_ms']:.2f}ms")
        logger.info(f"  P95: {stats['p95_ms']:.2f}ms")
        logger.info(f"  P99: {stats['p99_ms']:.2f}ms")

        return stats

    def get_results(self) -> List[Dict[str, Any]]:
        """Get all benchmark results"""
        return self.results

    def export_results(self, filepath: str) -> None:
        """Export results to JSON file"""
        with open(filepath, "w") as f:
            json.dump(self.results, f, indent=2)
        logger.info(f"Exported results to {filepath}")


if __name__ == "__main__":
    benchmark = QueryBenchmark()

    # Test benchmarking
    def test_query():
        time.sleep(0.01)  # Simulate query
        return "result"

    stats = benchmark.benchmark_query(test_query, "test_query", iterations=50)
    logger.info(json.dumps(stats, indent=2))
