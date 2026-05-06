#!/usr/bin/env bash
# NRG Audit Chain - Founder GPG Signing Script
# Creates detached ASCII-armored signatures for the 8 required milestone entries.

set -euo pipefail

REPO_ROOT="/Users/srujansai/Desktop/NRG"
AUDIT_DIR="${REPO_ROOT}/.audit"
CHAIN_FILE="${AUDIT_DIR}/chain.jsonl"
SIGNATURES_DIR="${AUDIT_DIR}/signatures"

declare -a ENTRIES=(
  "1:chain_genesis:genesis:46e3323a"
  "89:brute_force_attempt:dc012907:e2b9b33c"
  "356:consent_granted:3218dd3c:33f174b1"
  "357:consent_revoked:8f837c33:ffe320af"
  "375:data_erasure:0186bb3d:8f71b45f"
  "383:data_export:a515bab5:c2066160"
  "38302:chain_rebuild:1438e673:4c3a2170"
  "289837:ingest_batch:15cfed1e:f74b5d32"
)

echo "NRG founder GPG signing ceremony"
echo "Repo: ${REPO_ROOT}"
echo "UTC: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

if [[ ! -f "${CHAIN_FILE}" ]]; then
  echo "ERROR: ${CHAIN_FILE} not found" >&2
  exit 1
fi

if ! command -v gpg >/dev/null 2>&1; then
  echo "ERROR: gpg is not installed. Install with: brew install gnupg" >&2
  exit 1
fi

echo
echo "Available secret keys:"
gpg --list-secret-keys --keyid-format LONG || true

secret_count=$(gpg --list-secret-keys --keyid-format LONG 2>/dev/null | grep -c '^sec' || true)
if [[ "${secret_count}" -eq 0 ]]; then
  echo "ERROR: no founder secret key is available. Run: gpg --full-generate-key" >&2
  exit 1
fi

KEY_ID=""
if [[ "${secret_count}" -eq 1 ]]; then
  KEY_ID=$(gpg --list-secret-keys --keyid-format LONG 2>/dev/null | awk -F'[/ ]+' '/^sec/{print $3; exit}')
  echo "Using only available key: ${KEY_ID}"
else
  printf "Enter founder key id: "
  read -r KEY_ID
fi

if [[ -z "${KEY_ID}" ]]; then
  echo "ERROR: empty key id" >&2
  exit 1
fi

mkdir -p "${SIGNATURES_DIR}"

sign_count=0
verify_count=0

for idx in "${!ENTRIES[@]}"; do
  entry="${ENTRIES[$idx]}"
  IFS=':' read -r line_num expected_type expected_id expected_hash_prefix <<< "${entry}"
  ordinal=$(printf '%03d' "$((idx + 1))")
  entry_file="${SIGNATURES_DIR}/entry_${ordinal}_${expected_type}.json"
  sig_file="${entry_file}.asc"

  echo
  echo "Extracting line ${line_num}: ${expected_type}/${expected_id}"

  python3 - "${CHAIN_FILE}" "${line_num}" "${expected_type}" "${expected_id}" "${expected_hash_prefix}" > "${entry_file}" <<'PY'
import json
import sys
from pathlib import Path

chain_path = Path(sys.argv[1])
line_num = int(sys.argv[2])
expected_type = sys.argv[3]
expected_id = sys.argv[4]
expected_hash_prefix = sys.argv[5]

with chain_path.open() as fh:
    for current, line in enumerate(fh, 1):
        if current == line_num:
            entry = json.loads(line)
            break
    else:
        raise SystemExit(f"line {line_num} not found")

actual_type = entry.get("event_type")
actual_id = entry.get("event_id")
actual_hash = entry.get("hash", "")

if actual_type != expected_type or actual_id != expected_id or not actual_hash.startswith(expected_hash_prefix):
    raise SystemExit(
        f"entry mismatch at line {line_num}: "
        f"{actual_type}/{actual_id}/{actual_hash[:8]}"
    )

print(json.dumps(entry, sort_keys=True, separators=(",", ":")))
PY

  echo "Signing ${entry_file}"
  gpg --batch --yes --armor --detach-sign --local-user "${KEY_ID}" --output "${sig_file}" "${entry_file}"
  sign_count=$((sign_count + 1))

  echo "Verifying ${sig_file}"
  gpg --verify "${sig_file}" "${entry_file}"
  verify_count=$((verify_count + 1))
done

echo
echo "Signing complete: ${sign_count}/8 created, ${verify_count}/8 verified"
echo "Signature directory: ${SIGNATURES_DIR}"

if [[ "${sign_count}" -ne 8 || "${verify_count}" -ne 8 ]]; then
  echo "ERROR: signing ceremony incomplete" >&2
  exit 1
fi
