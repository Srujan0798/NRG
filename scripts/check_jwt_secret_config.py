#!/usr/bin/env python3
"""Fail if committed JWT_SECRET placeholders are shorter than 32 bytes."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

MIN_JWT_SECRET_BYTES = 32

ENV_JWT_SECRET_RE = re.compile(r"^\s*(JWT_SECRET)\s*=\s*(.*?)\s*$")
YAML_JWT_SECRET_RE = re.compile(
    r"^\s*(JWT_SECRET|jwtSecretPlaceholder)\s*:\s*(.*?)\s*$"
)


@dataclass(frozen=True)
class SecretFinding:
    path: Path
    line: int
    key: str
    byte_length: int
    message: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.key} {self.message} ({self.byte_length} bytes)"


def _clean_value(raw_value: str) -> str:
    value = raw_value.strip()
    if value.startswith(("'", '"')):
        quote = value[0]
        end = value.find(quote, 1)
        return value[1:end] if end != -1 else value[1:]
    value = value.split(" #", 1)[0].strip()
    if value.startswith("|") or value.startswith(">"):
        return ""
    return value


def _scan_line(path: Path, line_number: int, line: str) -> SecretFinding | None:
    matcher = ENV_JWT_SECRET_RE if path.name.startswith(".env") else YAML_JWT_SECRET_RE
    match = matcher.match(line)
    if not match:
        return None

    key, raw_value = match.groups()
    value = _clean_value(raw_value)
    byte_length = len(value.encode("utf-8"))
    if byte_length >= MIN_JWT_SECRET_BYTES:
        return None
    return SecretFinding(
        path=path,
        line=line_number,
        key=key,
        byte_length=byte_length,
        message=f"must be at least {MIN_JWT_SECRET_BYTES} bytes",
    )


def scan_config_paths(paths: list[Path]) -> list[SecretFinding]:
    findings: list[SecretFinding] = []
    for path in paths:
        if not path.exists():
            continue
        for line_number, line in enumerate(path.read_text().splitlines(), start=1):
            finding = _scan_line(path, line_number, line)
            if finding:
                findings.append(finding)
    return findings


def default_config_paths(repo_root: Path) -> list[Path]:
    return [
        repo_root / ".env.example",
        *sorted((repo_root / "infrastructure/helm/nrg").glob("values*.yaml")),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path, help="Config paths to scan")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    paths = args.paths or default_config_paths(repo_root)
    findings = scan_config_paths(paths)
    if findings:
        print("JWT secret config check failed:", file=sys.stderr)
        for finding in findings:
            print(finding, file=sys.stderr)
        return 1

    print("JWT secret config check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
