#!/usr/bin/env python3
"""Report evidence files older than a threshold without deleting anything."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_ROOT = REPO_ROOT / "evidence"


def report(max_age_days: int = 14) -> int:
    if not EVIDENCE_ROOT.exists():
        print("No evidence folder found.")
        return 0

    now = time.time()
    cutoff = max_age_days * 86400
    stale: list[tuple[Path, int]] = []
    total_bytes = 0

    for path in sorted(EVIDENCE_ROOT.rglob("*")):
        if not path.is_file():
            continue
        age_seconds = now - path.stat().st_mtime
        if age_seconds > cutoff:
            age_days = int(age_seconds / 86400)
            stale.append((path.relative_to(REPO_ROOT), age_days))
            total_bytes += path.stat().st_size

    if not stale:
        print("No stale evidence found.")
        return 0

    print(f"Found {len(stale)} stale evidence files ({total_bytes / (1024 * 1024):.1f} MB)")
    for rel_path, age_days in stale[:50]:
        print(f"  {rel_path} ({age_days} days)")
    if len(stale) > 50:
        print(f"  ... and {len(stale) - 50} more")
    print("No files were deleted.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Report stale NRG evidence files")
    parser.add_argument("--days", type=int, default=14, help="Max age in days")
    args = parser.parse_args()

    print(f"NRG Evidence Age Report - max age: {args.days} days")
    print("=" * 50)
    return report(max_age_days=args.days)


if __name__ == "__main__":
    sys.exit(main())
