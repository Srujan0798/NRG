#!/usr/bin/env python3
"""Verify the three critical-path acceptance personas.

The current auth backend keeps built-in acceptance personas in src.auth.jwt_handler.
This script is intentionally idempotent: it validates those users locally and
can optionally verify them against a running API.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.auth.jwt_handler import AuthError, get_jwt_handler  # noqa: E402


@dataclass(frozen=True)
class AcceptancePersona:
    email: str
    password: str
    role: str
    tier: int


PERSONAS = (
    AcceptancePersona("researcher@iitgn.ac.in", "Researcher@2026", "researcher", 1),
    AcceptancePersona("ministry@nrg.gov.in", "Ministry@2026", "government", 2),
    AcceptancePersona("partner@industry.in", "Industry@2026", "industry", 3),
)


def post_json(url: str, payload: dict[str, Any], timeout: float = 10.0) -> tuple[int, dict[str, Any]]:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {"detail": raw}
        return exc.code, data


def verify_local() -> list[dict[str, Any]]:
    handler = get_jwt_handler()
    results: list[dict[str, Any]] = []
    for persona in PERSONAS:
        user = handler.authenticate_user(persona.email, persona.password)
        if user["role"] != persona.role or user["tier"] != persona.tier:
            raise AuthError(f"{persona.email} resolved to {user['role']} tier {user['tier']}")
        results.append(
            {
                **asdict(persona),
                "user_id": user["user_id"],
                "status": "local-ready",
            }
        )
    return results


def verify_api(api_base: str) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for persona in PERSONAS:
        status, payload = post_json(
            f"{api_base.rstrip('/')}/auth/login",
            {"username": persona.email, "password": persona.password},
        )
        ok = (
            status == 200
            and payload.get("persona") == persona.role
            and payload.get("tier") == persona.tier
            and bool(payload.get("access_token"))
            and bool(payload.get("refresh_token"))
        )
        results.append(
            {
                **asdict(persona),
                "http_status": status,
                "user_id": payload.get("user_id"),
                "status": "api-ready" if ok else "api-failed",
                "detail": None if ok else payload,
            }
        )
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare and verify NRG acceptance personas.")
    parser.add_argument("--verify-api", metavar="URL", help="Also verify personas against a running API base URL.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()

    try:
        local_results = verify_local()
    except Exception as exc:
        print(f"Acceptance persona local verification failed: {exc}", file=sys.stderr)
        return 1

    api_results: list[dict[str, Any]] = []
    if args.verify_api:
        api_results = verify_api(args.verify_api)

    payload = {"local": local_results, "api": api_results}
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for item in local_results:
            print(f"LOCAL {item['status']}: {item['email']} -> tier {item['tier']} ({item['role']})")
        for item in api_results:
            print(f"API {item['status']}: {item['email']} -> tier {item['tier']} ({item['role']})")

    if any(item["status"] != "api-ready" for item in api_results):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
