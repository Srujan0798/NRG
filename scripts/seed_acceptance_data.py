#!/usr/bin/env python3
"""Acceptance data preflight.

This is a lightweight guard around the existing seed pipeline. It checks the
running API stats and reports whether the laptop has the expected critical-path
scale. In strict mode it fails when the data is below the acceptance floor.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TARGETS = {
    "researchers": 50_000,
    "publications": 50_000,
    "institutions": 181,
    "tables": 58,
}


def get_json(url: str, headers: dict[str, str] | None = None, timeout: float = 15.0) -> dict[str, Any]:
    req = urllib.request.Request(url, headers=headers or {}, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def post_json(url: str, payload: dict[str, Any], timeout: float = 15.0) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_stats(api_base: str) -> dict[str, int]:
    login_payload = post_json(
        f"{api_base.rstrip('/')}/auth/login",
        {"username": "researcher@iitgn.ac.in", "password": "Researcher@2026"},
    )
    token = login_payload["access_token"]
    stats = get_json(
        f"{api_base.rstrip('/')}/stats",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )
    health = get_json(f"{api_base.rstrip('/')}/health")
    database = health.get("database") or {}
    return {
        "researchers": int(stats.get("total_researchers") or stats.get("researchers") or database.get("researchers") or 0),
        "publications": int(stats.get("total_publications") or stats.get("publications") or database.get("publications") or 0),
        "institutions": int(stats.get("total_institutions") or stats.get("institutions") or 0),
        "tables": int(database.get("tables") or database.get("table_count") or 0),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check acceptance data readiness.")
    parser.add_argument("--api-base", default="http://localhost:8000", help="API base URL.")
    parser.add_argument("--strict", action="store_true", help="Fail if data is below acceptance targets.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()

    try:
        actuals = fetch_stats(args.api_base)
    except (urllib.error.URLError, urllib.error.HTTPError, KeyError, json.JSONDecodeError) as exc:
        print(f"Acceptance data preflight failed: {exc}", file=sys.stderr)
        return 1 if args.strict else 0

    checks = {
        key: {
            "actual": actuals.get(key, 0),
            "target": target,
            "ready": actuals.get(key, 0) >= target,
        }
        for key, target in TARGETS.items()
    }
    payload = {"checks": checks, "ready": all(item["ready"] for item in checks.values())}

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for key, item in checks.items():
            marker = "OK" if item["ready"] else "LOW"
            print(f"{marker} {key}: {item['actual']} / {item['target']}")

    if args.strict and not payload["ready"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
