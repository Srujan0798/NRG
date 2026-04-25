#!/usr/bin/env python3
"""NRG Load Test — 100 concurrent users via asyncio + httpx."""
import asyncio
import json
import os
import statistics
import sys
import time
from pathlib import Path

import httpx

# Source .env
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1)
                os.environ.setdefault(k, v)

API_BASE = "http://localhost:8000"
CONCURRENCY = 100
REQUESTS_PER_USER = 3
TIMEOUT = 30.0

PERSONAS = [
    ("researcher_user", os.getenv("RESEARCHER_PASSWORD", "researcher-pass"), "machine learning researchers in Gujarat"),
    ("gov_user", os.getenv("GOV_PASSWORD", "government-pass"), "total funding by state"),
    ("industry_user", os.getenv("INDUSTRY_PASSWORD", "industry-pass"), "top research areas"),
]

async def login(client, username, password):
    r = await client.post(
        f"{API_BASE}/login",
        json={"username": username, "password": password},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return r.json()["access_token"]

async def query(client, token, q):
    r = await client.post(
        f"{API_BASE}/query",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": q, "persona": "researcher"},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return r.json()

async def user_session(user_id: int):
    username, password, query_text = PERSONAS[user_id % len(PERSONAS)]
    times = []
    async with httpx.AsyncClient() as client:
        t0 = time.perf_counter()
        try:
            token = await login(client, username, password)
            times.append(("login", time.perf_counter() - t0))
        except Exception as e:
            times.append(("login_error", str(e)))
            return times

        for i in range(REQUESTS_PER_USER):
            t0 = time.perf_counter()
            try:
                data = await query(client, token, query_text)
                lat = time.perf_counter() - t0
                times.append((f"query_{i}", lat))
                if data.get("status") != "success":
                    times.append((f"query_{i}_error", data.get("error", "unknown")))
            except Exception as e:
                times.append((f"query_{i}_error", str(e)))
    return times

async def main():
    print(f"Starting load test: {CONCURRENCY} concurrent users x {REQUESTS_PER_USER} queries each")
    print(f"Total requests: ~{CONCURRENCY * (1 + REQUESTS_PER_USER)}")
    start = time.perf_counter()

    tasks = [asyncio.create_task(user_session(i)) for i in range(CONCURRENCY)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    total_time = time.perf_counter() - start

    all_query_latencies = []
    login_errors = 0
    query_errors = 0
    for r in results:
        if isinstance(r, Exception):
            login_errors += 1
            continue
        for name, val in r:
            if name == "login_error":
                login_errors += 1
            elif name.startswith("query_") and "error" in name:
                query_errors += 1
            elif name.startswith("query_") and isinstance(val, float):
                all_query_latencies.append(val)

    n = len(all_query_latencies)
    if n == 0:
        print("ZERO successful queries.")
        sys.exit(1)

    all_query_latencies.sort()
    p50 = all_query_latencies[int(n * 0.50)]
    p95 = all_query_latencies[min(int(n * 0.95), n - 1)]
    p99 = all_query_latencies[min(int(n * 0.99), n - 1)]
    mean = statistics.mean(all_query_latencies)

    print("\n" + "=" * 50)
    print("LOAD TEST RESULTS")
    print("=" * 50)
    print(f"Concurrent users:      {CONCURRENCY}")
    print(f"Total time:            {total_time:.1f}s")
    print(f"Successful logins:     {CONCURRENCY - login_errors}")
    print(f"Login errors:          {login_errors}")
    print(f"Successful queries:    {n}")
    print(f"Query errors:          {query_errors}")
    print(f"Mean latency:          {mean:.2f}s")
    print(f"p50 latency:           {p50:.2f}s")
    print(f"p95 latency:           {p95:.2f}s")
    print(f"p99 latency:           {p99:.2f}s")
    print(f"Throughput:            {n / total_time:.1f} queries/sec")
    print("=" * 50)

    out = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "concurrency": CONCURRENCY,
        "requests_per_user": REQUESTS_PER_USER,
        "total_time_s": round(total_time, 2),
        "successful_queries": n,
        "login_errors": login_errors,
        "query_errors": query_errors,
        "mean_latency_s": round(mean, 3),
        "p50_latency_s": round(p50, 3),
        "p95_latency_s": round(p95, 3),
        "p99_latency_s": round(p99, 3),
        "throughput_qps": round(n / total_time, 1),
    }
    Path("evidence").mkdir(exist_ok=True)
    today = time.strftime("%Y-%m-%d")
    Path(f"evidence/{today}").mkdir(exist_ok=True)
    with open(f"evidence/{today}/load_test_100users.json", "w") as f:
        json.dump(out, f, indent=2)
    print(f"Results saved to evidence/{today}/load_test_100users.json")

if __name__ == "__main__":
    asyncio.run(main())
