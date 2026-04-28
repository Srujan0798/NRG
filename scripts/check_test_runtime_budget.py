#!/usr/bin/env python3
"""Fail CI when test runtime exceeds the configured regression budget."""

from __future__ import annotations

import argparse


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-seconds", type=float, required=True)
    parser.add_argument("--baseline-seconds", type=float, required=True)
    parser.add_argument("--max-growth", type=float, default=0.20)
    parser.add_argument("--absolute-max-seconds", type=float, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    regression_limit = args.baseline_seconds * (1 + args.max_growth)
    limits = [regression_limit]
    if args.absolute_max_seconds is not None:
        limits.append(args.absolute_max_seconds)
    effective_limit = min(limits)

    print(
        "Test runtime: "
        f"{args.runtime_seconds:.1f}s; baseline={args.baseline_seconds:.1f}s; "
        f"20% regression limit={regression_limit:.1f}s"
    )

    if args.runtime_seconds > effective_limit:
        print(
            "FAILED: test runtime budget exceeded "
            f"({args.runtime_seconds:.1f}s > {effective_limit:.1f}s)"
        )
        return 1

    print("PASSED: test runtime budget within limit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
