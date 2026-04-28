#!/usr/bin/env python3
"""CI/pre-commit audit-chain verifier."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.audit import verify_chain


def main() -> int:
    valid, errors, count = verify_chain()
    payload = {
        "ok": valid,
        "valid": valid,
        "valid_event_count": count,
        "errors": errors,
    }
    print(json.dumps(payload, indent=2))
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
