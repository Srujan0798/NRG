"""Measure live /query latency and write K-4 evidence JSON."""

from __future__ import annotations

import argparse
import json
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


DEFAULT_QUERY = "How many IIT papers published in 2023?"
DEFAULT_OUTPUT = Path("evidence/2026-04-28/cold_query_latency.json")


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round((pct / 100) * (len(ordered) - 1)))))
    return ordered[index]


def login(base_url: str, username: str, password: str, timeout: float, client_ip: str) -> str:
    response = requests.post(
        f"{base_url.rstrip('/')}/auth/login",
        headers={"X-Forwarded-For": client_ip},
        json={"username": username, "password": password},
        timeout=timeout,
    )
    response.raise_for_status()
    token = response.json().get("access_token")
    if not token:
        raise RuntimeError("Login response did not include access_token")
    return token


def run_query(
    base_url: str,
    token: str,
    query: str,
    index: int,
    timeout: float,
    client_ip: str,
) -> dict[str, Any]:
    start = time.perf_counter()
    response = requests.post(
        f"{base_url.rstrip('/')}/query",
        headers={"Authorization": f"Bearer {token}", "X-Forwarded-For": client_ip},
        json={"query": query, "session_id": f"k4-cold-query-bench-{index}"},
        timeout=timeout,
    )
    elapsed_ms = (time.perf_counter() - start) * 1000
    payload: dict[str, Any] = {}
    try:
        payload = response.json()
    except Exception:
        payload = {}
    return {
        "index": index,
        "status_code": response.status_code,
        "latency_ms": round(elapsed_ms, 2),
        "routing_decision": payload.get("routing_decision"),
        "intent": payload.get("intent"),
        "node_timings": payload.get("node_timings", {}),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="http://localhost:8000")
    parser.add_argument("--queries", type=int, default=20)
    parser.add_argument("--query", default=DEFAULT_QUERY)
    parser.add_argument("--username", default="researcher_user")
    parser.add_argument("--password", default="researcher-pass")
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument("--client-ip-prefix", default="10.241.4")
    parser.add_argument("--sleep-seconds", type=float, default=0.0)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    samples = []
    for index in range(args.queries):
        client_ip = f"{args.client_ip_prefix}.{index + 1}"
        token = login(args.host, args.username, args.password, args.timeout, client_ip)
        samples.append(
            run_query(
                args.host,
                token,
                args.query,
                index + 1,
                args.timeout,
                client_ip,
            )
        )
        if args.sleep_seconds and index < args.queries - 1:
            time.sleep(args.sleep_seconds)
    latencies = [sample["latency_ms"] for sample in samples if sample["status_code"] == 200]
    failures = [sample for sample in samples if sample["status_code"] != 200]
    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "protocol": "K-4",
        "host": args.host,
        "query": args.query,
        "sample_count": len(samples),
        "successful_samples": len(latencies),
        "failure_count": len(failures),
        "p50_latency_ms": round(statistics.median(latencies), 2) if latencies else None,
        "p95_latency_ms": round(percentile(latencies, 95), 2) if latencies else None,
        "p99_latency_ms": round(percentile(latencies, 99), 2) if latencies else None,
        "max_latency_ms": round(max(latencies), 2) if latencies else None,
        "target_p99_ms": 500,
        "status": "PASS" if latencies and percentile(latencies, 99) < 500 and not failures else "FAIL",
        "samples": samples,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
