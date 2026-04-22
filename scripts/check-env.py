#!/usr/bin/env python3
"""Pre-commit hook to prevent .env from having CLOUD_SYNTHESIS_ALLOWED=false."""

import os
import sys
import re
from pathlib import Path


def check_env_file(env_path: Path) -> bool:
    """Check if CLOUD_SYNTHESIS_ALLOWED is set to false in .env file."""
    if not env_path.exists():
        return True

    content = env_path.read_text()

    for line in content.splitlines():
        line = line.strip()
        if line.startswith("#") or not line:
            continue
        if "CLOUD_SYNTHESIS_ALLOWED" in line and "=" in line:
            value = line.split("=", 1)[1].strip()
            if value.lower() not in ("true", "1", "yes"):
                print(f"ERROR: CLOUD_SYNTHESIS_ALLOWED must be 'true' in committed .env")
                print(f"  Line: {line}")
                print(f"  Current value '{value}' is not allowed — LLM synthesis requires 'true'")
                print(f"  If testing rate-limiting locally, set NRG_QUOTA_DISABLED=1 instead")
                return False
    return True


def check_staged_files() -> bool:
    """Check if any staged .env file has CLOUD_SYNTHESIS_ALLOWED=false."""
    import subprocess

    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--", ".env"],
            capture_output=True,
            text=True,
            check=False,
        )
        staged_env_files = result.stdout.strip().split("\n")

        for env_file in staged_env_files:
            env_path = Path(env_file)
            if env_path.exists() and not check_env_file(env_path):
                return False
    except Exception as e:
        print(f"Warning: Could not check staged files: {e}")

    return True


def main() -> int:
    """Main entry point."""
    env_path = Path(".env")

    if not check_env_file(env_path):
        return 1

    if not check_staged_files():
        return 1

    print("OK: CLOUD_SYNTHESIS_ALLOWED check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
