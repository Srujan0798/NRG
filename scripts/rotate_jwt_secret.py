#!/usr/bin/env python3
"""Generate a production-strength JWT_SECRET for emergency rotation."""

from __future__ import annotations

import argparse
import os
import secrets
import stat
import sys
from pathlib import Path

MIN_JWT_SECRET_BYTES = 32


def generate_jwt_secret(num_bytes: int = MIN_JWT_SECRET_BYTES) -> str:
    """Generate a URL-safe random secret with at least num_bytes of entropy."""
    if num_bytes < MIN_JWT_SECRET_BYTES:
        raise ValueError(f"JWT secret entropy must be at least {MIN_JWT_SECRET_BYTES} bytes")
    return secrets.token_urlsafe(num_bytes)


def write_secret_file(path: Path, secret: str, env_format: bool = True) -> None:
    """Write the rotated secret to a chmod 600 file."""
    path.write_text(f"JWT_SECRET={secret}\n" if env_format else f"{secret}\n")
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a 32+ byte JWT_SECRET for rotation")
    parser.add_argument("--bytes", type=int, default=MIN_JWT_SECRET_BYTES, help="Entropy bytes to generate")
    parser.add_argument("--output", type=Path, help="Write secret to file with chmod 600")
    parser.add_argument("--raw", action="store_true", help="Print/write only the secret value")
    args = parser.parse_args()

    try:
        secret = generate_jwt_secret(args.bytes)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.output:
        write_secret_file(args.output, secret, env_format=not args.raw)
        print(f"Wrote JWT secret to {args.output} ({len(secret.encode('utf-8'))} bytes)")
        return 0

    if args.raw:
        print(secret)
    else:
        print(f"JWT_SECRET={secret}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
