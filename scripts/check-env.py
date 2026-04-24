#!/usr/bin/env python3
"""Pre-commit hook to validate the cloud synthesis opt-in flag."""

import sys
from pathlib import Path


TRUE_VALUES = {"true", "1", "yes"}
FALSE_VALUES = {"false", "0", "no"}
BOOLEAN_VALUES = TRUE_VALUES | FALSE_VALUES


def check_env_file(env_path: Path) -> bool:
    """Check CLOUD_SYNTHESIS_ALLOWED is a valid explicit boolean when present."""
    if not env_path.exists():
        return True

    content = env_path.read_text()

    for line in content.splitlines():
        line = line.strip()
        if line.startswith("#") or not line:
            continue
        if line.startswith("CLOUD_SYNTHESIS_ALLOWED") and "=" in line:
            value = line.split("=", 1)[1].strip()
            if value.lower() not in BOOLEAN_VALUES:
                print("ERROR: CLOUD_SYNTHESIS_ALLOWED must be a boolean")
                print(f"  Line: {line}")
                print(f"  Current value '{value}' is not valid")
                print("  Use 'false' for the sovereign/local default or 'true' for explicit cloud opt-in")
                return False
    return True


def check_staged_files() -> bool:
    """Check if any staged .env file has a valid CLOUD_SYNTHESIS_ALLOWED value."""
    import subprocess

    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--", ".env"],
            capture_output=True,
            text=True,
            check=False,
        )
        staged_env_files = [name for name in result.stdout.splitlines() if name.strip()]

        for env_file in staged_env_files:
            env_path = Path(env_file)
            if env_path.is_file() and not check_env_file(env_path):
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

    print("OK: CLOUD_SYNTHESIS_ALLOWED boolean check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
