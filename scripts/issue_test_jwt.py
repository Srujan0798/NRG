#!/usr/bin/env python3
"""Issue an acceptance JWT for local smoke tests."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.auth.jwt_handler import JWTHandler  # noqa: E402


PERSONA_CREDENTIALS = {
    "researcher": ("researcher@iitgn.ac.in", "Researcher@2026"),
    "government": ("ministry@nrg.gov.in", "Ministry@2026"),
    "industry": ("partner@industry.in", "Industry@2026"),
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Issue a local acceptance JWT.")
    parser.add_argument("persona", choices=sorted(PERSONA_CREDENTIALS), help="Persona to issue.")
    parser.add_argument("--refresh", action="store_true", help="Print refresh token instead of access token.")
    parser.add_argument("--json", action="store_true", help="Print full token payload as JSON.")
    args = parser.parse_args()

    username, password = PERSONA_CREDENTIALS[args.persona]
    handler = JWTHandler()
    user = handler.authenticate_user(username, password)
    tokens = handler.issue_token_pair(user)
    payload = {
        "persona": args.persona,
        "username": username,
        "user_id": user["user_id"],
        "tier": user["tier"],
        **tokens,
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    print(tokens["refresh_token"] if args.refresh else tokens["access_token"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
