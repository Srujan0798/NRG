#!/usr/bin/env python3
"""Investigate HMAC audit-chain integrity breaks."""

from __future__ import annotations

import argparse
import hmac
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from src.audit import AuditEvent


def investigate_chain(
    chain_path: str | Path = ".audit/chain.jsonl",
    since: str | None = None,
    chain_key: str | None = None,
) -> dict[str, Any]:
    path = Path(chain_path)
    if not path.exists():
        return {"ok": True, "events_checked": 0, "broken_indices": [], "message": "chain missing"}

    key = chain_key or os.getenv("AUDIT_CHAIN_KEY") or "nrg-audit-chain-dev-key"
    since_dt = datetime.fromisoformat(since) if since else None
    prev_hash = "0" * 64
    broken: list[int] = []
    checked = 0

    for index, line in enumerate(path.read_text().splitlines(), 1):
        event = json.loads(line)
        timestamp = event.get("timestamp")
        if since_dt and timestamp:
            try:
                if datetime.fromisoformat(timestamp) < since_dt:
                    prev_hash = event.get("hash", prev_hash)
                    continue
            except ValueError:
                pass

        recorded_hash = event.get("hash")
        event_kwargs = {
            k: v
            for k, v in event.items()
            if k not in ("hash", "per_user_binding", "user_key_hash")
        }
        if "_v" not in event:
            event_kwargs["_v"] = None
        serialized = AuditEvent(**event_kwargs).serialize()
        computed = hmac.new(
            key.encode(),
            (prev_hash + serialized).encode(),
            hashlib.sha256,
        ).hexdigest()
        if computed != recorded_hash:
            broken.append(index)
        prev_hash = recorded_hash or prev_hash
        checked += 1

    return {"ok": not broken, "events_checked": checked, "broken_indices": broken}


def main() -> int:
    parser = argparse.ArgumentParser(description="Investigate NRG audit chain")
    parser.add_argument("--chain-path", default=".audit/chain.jsonl")
    parser.add_argument("--since", default=None)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    result = investigate_chain(args.chain_path, args.since)
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
