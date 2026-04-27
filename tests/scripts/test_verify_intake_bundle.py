import csv
import json

from scripts.verify_intake_bundle import (
    compute_row_hmac,
    verify_bundle,
    verify_csv_hmacs,
)


def _write_csv(path, rows):
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def test_verify_csv_hmacs_accepts_valid_rows(tmp_path):
    secret = "intake-secret"
    row = {"researcher_id": "r1", "name": "Asha", "state": "Gujarat"}
    row["row_hmac"] = compute_row_hmac(row, secret)
    csv_path = tmp_path / "researchers.csv"
    _write_csv(csv_path, [row])

    result = verify_csv_hmacs(csv_path, secret)

    assert result["valid_rows"] == 1
    assert result["invalid_rows"] == 0


def test_verify_csv_hmacs_reports_invalid_rows(tmp_path):
    row = {"researcher_id": "r1", "name": "Asha", "state": "Gujarat", "row_hmac": "bad"}
    csv_path = tmp_path / "researchers.csv"
    _write_csv(csv_path, [row])

    result = verify_csv_hmacs(csv_path, "intake-secret")

    assert result["valid_rows"] == 0
    assert result["invalid_rows"] == 1


def test_verify_bundle_checks_manifest_hash_and_hmac(tmp_path):
    secret = "intake-secret"
    row = {"researcher_id": "r1", "name": "Asha", "state": "Gujarat"}
    row["row_hmac"] = compute_row_hmac(row, secret)
    csv_path = tmp_path / "researchers.csv"
    _write_csv(csv_path, [row])

    import hashlib

    digest = hashlib.sha256(csv_path.read_bytes()).hexdigest()
    manifest = {
        "files": [
            {
                "path": "researchers.csv",
                "sha256": digest,
                "bytes": csv_path.stat().st_size,
                "table": "researchers",
            }
        ]
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest))

    result = verify_bundle(tmp_path, manifest_path, hmac_secret=secret, skip_gpg=True)

    assert result["status"] == "pass"
    assert result["files_verified"] == 1
    assert result["hmac"]["invalid_rows"] == 0
