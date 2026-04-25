#!/usr/bin/env python3
"""
UAT Session Runner — All 3 Tiers.

Orchestrates all 3 UAT sessions in sequence, collects results,
and generates the final UAT attestation.

Usage:
    python scripts/uat_run_session.py --all
    python scripts/uat_run_session.py --tier 1
    python scripts/uat_run_session.py --tier 1 --host http://localhost:8000
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, UTC
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "evidence"
UAT_DIR = ROOT / "docs" / "handover"

TIERS = {
    "1": {
        "name": "Professor (Tier 1 Researcher)",
        "user": "researcher_user",
        "pass": "researcher-pass",
        "queries": 10,
        "output": "03_uat_t1.md",
        "login_url": "/auth/login",
        "query_url": "/api/query/stream",
    },
    "2": {
        "name": "Ministry Liaison (Tier 2 Government)",
        "user": "gov_user",
        "pass": "government-pass",
        "queries": 10,
        "output": "03_uat_t2.md",
        "login_url": "/auth/login",
        "query_url": "/api/query/stream",
    },
    "3": {
        "name": "Industry Partner (Tier 3 Industry)",
        "user": "industry_user",
        "pass": "industry-pass",
        "queries": 10,
        "output": "03_uat_t3.md",
        "login_url": "/auth/login",
        "query_url": "/api/query/stream",
    },
}


def get_token(host: str, user: str, password: str) -> str:
    """Login and get JWT token."""
    import urllib.request
    req = urllib.request.Request(
        f"{host}/auth/login",
        data=json.dumps({"username": user, "password": password}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
        return data.get("access_token") or data.get("token", "")


def run_query(host: str, token: str, query: str, timeout: int = 30) -> dict:
    """Run a single query and return timing + result."""
    import urllib.request
    start = time.time()
    try:
        req = urllib.request.Request(
            f"{host}/api/query/stream",
            data=json.dumps({"query": query, "session_id": "uat"}).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            elapsed = time.time() - start
            body = resp.read().decode()
            try:
                result = json.loads(body)
            except Exception:
                result = {"text": body[:500]}
            return {
                "query": query,
                "elapsed_sec": round(elapsed, 2),
                "status": "success",
                "result": result,
            }
    except Exception as e:
        return {
            "query": query,
            "elapsed_sec": round(time.time() - start, 2),
            "status": "error",
            "error": str(e),
        }


def run_tier(
    tier: str,
    host: str,
    output_path: Path,
    skip_login: bool = False,
) -> dict:
    """Run UAT session for one tier."""
    cfg = TIERS[tier]
    print(f"\n{'='*60}")
    print(f"UAT SESSION — {cfg['name']}")
    print(f"{'='*60}")

    if not skip_login:
        print(f"\n[1/3] Logging in as {cfg['user']}...")
        try:
            token = get_token(host, cfg["user"], cfg["pass"])
            print(f"  ✅ Logged in. Token: {token[:20]}...")
        except Exception as e:
            print(f"  ❌ Login failed: {e}")
            return {"tier": tier, "status": "FAIL", "login_error": str(e)}
    else:
        token = None
        print(f"  ⏭️  Skipping login (host mode)")

    print(f"\n[2/3] Running {cfg['queries']} queries...")
    results = []

    queries = get_queries_for_tier(tier)
    for i, q in enumerate(queries, 1):
        print(f"  [{i}/{cfg['queries']}] {q[:60]}...")
        r = run_query(host, token, q)
        results.append(r)
        print(f"    → {r['elapsed_sec']}s  {r['status']}")
        time.sleep(0.5)  # Brief pause between queries

    print(f"\n[3/3] Verifying audit chain...")
    try:
        from src.audit import verify_chain
        valid, errs, count = verify_chain()
        chain_status = "✅ VALID" if valid else f"❌ INVALID ({errs})"
        print(f"  {chain_status} — {count} events")
    except Exception as e:
        chain_status = f"❌ Error: {e}"

    # Write results
    now = datetime.now(UTC).isoformat()
    output = {
        "tier": tier,
        "timestamp": now,
        "user": cfg["user"],
        "results": results,
        "chain_status": chain_status,
        "summary": {
            "total": len(results),
            "success": sum(1 for r in results if r["status"] == "success"),
            "errors": sum(1 for r in results if r["status"] == "error"),
            "avg_time": round(sum(r["elapsed_sec"] for r in results) / len(results), 2) if results else 0,
        },
    }

    output_path.write_text(json.dumps(output, indent=2, default=str))
    print(f"\n  Results → {output_path}")

    return output


def get_queries_for_tier(tier: str) -> list[str]:
    """Return the 10 canonical UAT queries for each tier."""
    if tier == "1":
        return [
            "find robotics researchers in Gujarat",
            "Who has published the most on machine learning in the last 5 years?",
            "Show me researchers working on hydrogen fuel cells",
            "Compare AI research output between Gujarat and Karnataka over the last 5 years",
            "Find my profile and show my publications",
            "Which institutions have the highest collaboration rate?",
            "Show me labs working on quantum computing",
            "What is the funding trend for renewable energy research?",
            "Find researchers who have patents in semiconductor design",
            "Show the knowledge graph for deep learning",
        ]
    elif tier == "2":
        return [
            "Show state-wise research funding for the last 3 years",
            "Which states have the most publications in AI?",
            "What percentage of research is in healthcare vs engineering?",
            "Show the growth trend of IIT publications over 10 years",
            "Which institutions have the highest patents filed?",
            "Compare funding allocation between government and private institutions",
            "What is the research output per crore of funding?",
            "Show the geographic distribution of renewable energy research",
            "Which research areas have grown the fastest in 5 years?",
            "Generate a summary report of national research capacity",
        ]
    else:
        return [
            "Who works on electric vehicle battery technology?",
            "Find institutions with semiconductor research capability",
            "Who are the top experts in machine learning?",
            "Show research groups working on quantum computing",
            "Which institutions collaborate on robotics research?",
            "Find researchers in graphene-related technologies",
            "Who has expertise in chip design and verification?",
            "Show the top 10 research institutions in India by area",
            "Which researchers publish on 5G and next-gen communications?",
            "Find industry-academia collaboration examples in AI",
        ]


def main():
    parser = argparse.ArgumentParser(description="NRG UAT Session Runner")
    parser.add_argument("--tier", choices=["1", "2", "3"], help="Run specific tier only")
    parser.add_argument("--all", action="store_true", help="Run all 3 tiers")
    parser.add_argument("--host", default="http://localhost:8000", help="API host")
    parser.add_argument("--skip-login", action="store_true", help="Skip login (host mode)")
    args = parser.parse_args()

    if not args.tier and not args.all:
        parser.print_help()
        sys.exit(1)

    tiers_to_run = [args.tier] if args.tier else ["1", "2", "3"]
    results = []

    for tier in tiers_to_run:
        cfg = TIERS[tier]
        output_path = EVIDENCE_DIR / f"03_uat_t{tier}_results.json"
        r = run_tier(tier, args.host, output_path, args.skip_login)
        results.append(r)

    # Summary
    print(f"\n{'='*60}")
    print("UAT SUMMARY")
    print(f"{'='*60}")
    for r in results:
        s = r.get("summary", {})
        print(f"  Tier {r['tier']}: {s.get('success','?')}/{s.get('total','?')} queries OK, "
              f"avg {s.get('avg_time','?')}s — {r.get('chain_status', '?')}")

    # Write combined attestation
    combined = {
        "timestamp": datetime.now(UTC).isoformat(),
        "tiers": results,
        "overall_pass": all(
            r.get("summary", {}).get("success", 0) >= 8 for r in results
        ),
    }
    (EVIDENCE_DIR / "03_uat_all_results.json").write_text(json.dumps(combined, indent=2))
    print(f"\n  Combined → {EVIDENCE_DIR / '03_uat_all_results.json'}")


if __name__ == "__main__":
    main()
