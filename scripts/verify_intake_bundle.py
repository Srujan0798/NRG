#!/usr/bin/env python3
"""Verify a ministry intake bundle before loading it into PostgreSQL.

Checks:
- Manifest file count, byte count, and SHA-256 digest.
- Optional GPG detached sidecar signatures (.asc or .sig).
- Per-row HMAC in CSV files using a row_hmac column.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import hmac
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


def _canonical_row(row: dict[str, Any]) -> bytes:
    canonical = {
        key: value
        for key, value in row.items()
        if key not in {"row_hmac", "hmac", "signature"}
    }
    return json.dumps(canonical, sort_keys=True, separators=(",", ":"), default=str).encode()


def compute_row_hmac(row: dict[str, Any], secret: str) -> str:
    return hmac.new(secret.encode(), _canonical_row(row), hashlib.sha256).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_csv_hmacs(path: Path, secret: str) -> dict[str, Any]:
    valid_rows = 0
    invalid_rows = 0
    checked_rows = 0
    first_errors: list[dict[str, Any]] = []

    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or "row_hmac" not in reader.fieldnames:
            return {
                "file": str(path),
                "checked_rows": 0,
                "valid_rows": 0,
                "invalid_rows": 0,
                "skipped": True,
                "reason": "row_hmac column missing",
            }
        for line_number, row in enumerate(reader, start=2):
            checked_rows += 1
            expected = str(row.get("row_hmac", "")).strip().lower()
            actual = compute_row_hmac(row, secret)
            if hmac.compare_digest(expected, actual):
                valid_rows += 1
            else:
                invalid_rows += 1
                if len(first_errors) < 10:
                    first_errors.append({"line": line_number, "expected": expected, "actual": actual})

    return {
        "file": str(path),
        "checked_rows": checked_rows,
        "valid_rows": valid_rows,
        "invalid_rows": invalid_rows,
        "first_errors": first_errors,
    }


def _find_signature(path: Path) -> Path | None:
    for suffix in (".asc", ".sig"):
        candidate = path.with_name(path.name + suffix)
        if candidate.exists():
            return candidate
    return None


def verify_gpg_signature(path: Path) -> dict[str, Any]:
    signature = _find_signature(path)
    if signature is None:
        return {"status": "fail", "file": str(path), "reason": "missing .asc/.sig sidecar"}

    result = subprocess.run(
        ["gpg", "--verify", str(signature), str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "status": "pass" if result.returncode == 0 else "fail",
        "file": str(path),
        "signature": str(signature),
        "stderr": result.stderr[-1000:],
    }


def verify_bundle(
    bundle_dir: Path,
    manifest_path: Path,
    hmac_secret: str,
    skip_gpg: bool = False,
) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text())
    files = manifest.get("files", [])
    failures: list[dict[str, Any]] = []
    gpg_results: list[dict[str, Any]] = []
    hmac_totals = {"checked_rows": 0, "valid_rows": 0, "invalid_rows": 0}
    files_verified = 0

    for item in files:
        rel_path = Path(item["path"])
        path = bundle_dir / rel_path
        if not path.exists():
            failures.append({"file": str(rel_path), "reason": "missing"})
            continue

        expected_bytes = item.get("bytes")
        if expected_bytes is not None and path.stat().st_size != int(expected_bytes):
            failures.append({"file": str(rel_path), "reason": "byte_count_mismatch"})

        expected_sha = str(item.get("sha256", "")).lower()
        actual_sha = sha256_file(path)
        if expected_sha and actual_sha != expected_sha:
            failures.append({"file": str(rel_path), "reason": "sha256_mismatch"})

        if not skip_gpg:
            gpg_result = verify_gpg_signature(path)
            gpg_results.append(gpg_result)
            if gpg_result["status"] != "pass":
                failures.append({"file": str(rel_path), "reason": "gpg_signature_failed"})

        if path.suffix.lower() == ".csv":
            hmac_result = verify_csv_hmacs(path, hmac_secret)
            for key in hmac_totals:
                hmac_totals[key] += int(hmac_result.get(key, 0) or 0)
            if hmac_result.get("invalid_rows", 0):
                failures.append({"file": str(rel_path), "reason": "row_hmac_failed", "details": hmac_result})

        files_verified += 1

    return {
        "status": "pass" if not failures else "fail",
        "manifest": str(manifest_path),
        "bundle_dir": str(bundle_dir),
        "files_expected": len(files),
        "files_verified": files_verified,
        "failures": failures,
        "gpg": gpg_results,
        "hmac": hmac_totals,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify NRG ministry intake bundle")
    parser.add_argument("--bundle-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--hmac-secret-env", default="DATA_INTAKE_HMAC_SECRET")
    parser.add_argument("--skip-gpg", action="store_true", help="Skip GPG verification for local dry runs")
    args = parser.parse_args()

    secret = os.getenv(args.hmac_secret_env)
    if not secret:
        print(f"Missing required HMAC secret env var: {args.hmac_secret_env}", file=sys.stderr)
        return 2

    result = verify_bundle(args.bundle_dir, args.manifest, secret, skip_gpg=args.skip_gpg)
    print(json.dumps(result, indent=2, default=str))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
