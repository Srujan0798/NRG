#!/usr/bin/env python3
"""
Pre-warm NRG API cache with demo queries.
Run this 10-15 minutes before any demo.

Usage:
    python scripts/prewarm_demo_cache.py --tier researcher
    python scripts/prewarm_demo_cache.py --tier government
    python scripts/prewarm_demo_cache.py --tier industry
    python scripts/prewarm_demo_cache.py --all

The API uses an in-memory TTL cache (30s default).
Warming ensures <1s response times for repeated queries.
"""

import argparse
import asyncio
import json
import time
import urllib.request
from typing import List, Tuple

API_BASE = "http://localhost:8000"

# Working demo queries by tier — these trigger the fast-path planner
DEMO_QUERIES = {
    "researcher": [
        "Which IIT has the highest total innovation credits in FY 2022-23",
        "Top 5 funding agencies by total grant amount",
        "Show me researchers working on machine learning",
        "Which institutes in India have the highest grant amount in renewable energy",
        "Compare AI research output between Gujarat and Karnataka",
        "Identify 3 institutes that cut grants >40% YoY yet increased granted patents",
        "For IIT Madras, what % of innovations moved from Lab Validation to Market Ready",
    ],
    "government": [
        "Which states have the highest renewable energy research output",
        "Compare AI research output between Gujarat and Karnataka over the last 5 years",
        "Top 5 funding agencies by total grant amount",
        "Which IIT has the highest total innovation credits in FY 2022-23",
    ],
    "industry": [
        "What AI capabilities do Indian research institutions offer",
        "Find industry-academia collaboration examples in renewable energy",
        "Which institutions are strongest for semiconductor partnerships",
    ],
}

CREDENTIALS = {
    "researcher": ("researcher_user", "researcher-pass"),
    "government": ("gov_user", "government-pass"),
    "industry": ("industry_user", "industry-pass"),
}


def get_token(username: str, password: str) -> str:
    req = urllib.request.Request(
        f"{API_BASE}/login",
        data=json.dumps({"username": username, "password": password}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    resp = urllib.request.urlopen(req, timeout=10)
    data = json.loads(resp.read())
    return data["access_token"]


def warm_query(token: str, query: str) -> Tuple[str, float, str]:
    req = urllib.request.Request(
        f"{API_BASE}/query",
        data=json.dumps({"question": query}).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    start = time.time()
    try:
        resp = urllib.request.urlopen(req, timeout=60)
        data = json.loads(resp.read())
        elapsed = time.time() - start
        status = data.get("status", "unknown")
        return status, elapsed, ""
    except Exception as e:
        elapsed = time.time() - start
        return "error", elapsed, str(e)


def prewarm_tier(tier: str) -> None:
    username, password = CREDENTIALS[tier]
    print(f"\n{'='*60}")
    print(f"Pre-warming: {tier.upper()}")
    print(f"{'='*60}")

    token = get_token(username, password)
    queries = DEMO_QUERIES.get(tier, [])

    total_time = 0.0
    success_count = 0

    for i, query in enumerate(queries, 1):
        status, elapsed, err = warm_query(token, query)
        total_time += elapsed
        ok = status == "success" and not err
        if ok:
            success_count += 1
        marker = "✅" if ok else "❌"
        print(f"{marker} [{i}/{len(queries)}] {elapsed:.1f}s — {query[:60]}...")
        if err:
            print(f"   Error: {err[:100]}")

    print(f"\nSummary: {success_count}/{len(queries)} warmed in {total_time:.1f}s")
    if success_count == len(queries):
        print("🎯 All queries cached. Demo responses will be <1s.")
    else:
        print("⚠️  Some queries failed. Review errors above.")


def main():
    parser = argparse.ArgumentParser(description="Pre-warm NRG demo cache")
    parser.add_argument("--tier", choices=["researcher", "government", "industry"], help="Tier to warm")
    parser.add_argument("--all", action="store_true", help="Warm all tiers")
    args = parser.parse_args()

    if args.all:
        for tier in ["researcher", "government", "industry"]:
            prewarm_tier(tier)
    elif args.tier:
        prewarm_tier(args.tier)
    else:
        print("Usage: python scripts/prewarm_demo_cache.py --tier researcher")
        print("       python scripts/prewarm_demo_cache.py --all")


if __name__ == "__main__":
    main()
