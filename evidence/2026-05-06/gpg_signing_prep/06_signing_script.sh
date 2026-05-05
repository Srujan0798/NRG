#!/bin/bash
# NRG Audit Chain - Founder GPG Signing Script
# Date: 2026-05-06
# Purpose: Sign 8 milestone audit chain entries with founder GPG key

set -e

echo "=========================================="
echo "NRG GPG Signing Ceremony"
echo "Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "=========================================="

# Configuration
AUDIT_DIR="/Users/srujansai/Desktop/NRG/.audit"
SIGNATURES_DIR="${AUDIT_DIR}/signatures"
CHAIN_FILE="${AUDIT_DIR}/chain.jsonl"
VENV_BIN="/Users/srujansai/Desktop/NRG/.venv/bin"

# Entry definitions: (line_number, event_type, event_id, short_hash)
# Line numbers are 1-indexed for human readability, 0-indexed for array access
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

# Step 1: Check GPG installation
echo ""
echo "[1/6] Checking GPG installation..."
if ! command -v gpg &> /dev/null; then
    echo "ERROR: GPG is not installed."
    echo "Please install GPG first:"
    echo "  macOS: brew install gnupg"
    echo "  Ubuntu: sudo apt-get install gnupg"
    exit 1
fi
echo "GPG found: $(gpg --version | head -n1)"

# Step 2: Check for secret keys
echo ""
echo "[2/6] Checking for secret keys..."
SECRET_KEYS=$(gpg --list-secret-keys --keyid-format LONG 2>/dev/null | grep -c "sec" || true)
if [ "$SECRET_KEYS" -eq 0 ]; then
    echo "ERROR: No secret keys found."
    echo "Please generate a GPG key first by running:"
    echo "  gpg --full-generate-key"
    echo ""
    echo "Recommended settings:"
    echo "  - Key type: RSA and RSA"
    echo "  - Key size: 4096"
    echo "  - Expiration: None"
    echo "  - Name: Founder NRG"
    echo "  - Email: founder@iitgn.ac.in"
    exit 1
fi
echo "Found $SECRET_KEYS secret key(s)"

# List available keys
echo ""
echo "Available secret keys:"
gpg --list-secret-keys --keyid-format LONG 2>/dev/null | grep -A2 "sec" || true

# Step 3: Prompt for key ID if multiple exist
echo ""
echo "[3/6] Selecting signing key..."
KEY_ID=""
if [ "$SECRET_KEYS" -eq 1 ]; then
    # Only one key, extract the key ID automatically
    KEY_ID=$(gpg --list-secret-keys --keyid-format LONG 2>/dev/null | grep "sec" | sed -n 's/.*rsa4096\/\([A-F0-9]*\).*/\1/p' | head -1)
    echo "Using only available key: $KEY_ID"
else
    echo "Multiple keys found. Please specify which key to use:"
    echo "Enter the key ID (the 16-character hex string after rsa4096/):"
    read -r KEY_ID
    if [ -z "$KEY_ID" ]; then
        echo "ERROR: No key ID specified"
        exit 1
    fi
fi

# Step 4: Create signatures directory
echo ""
echo "[4/6] Creating signatures directory..."
mkdir -p "${SIGNATURES_DIR}"
echo "Signatures will be stored in: ${SIGNATURES_DIR}"

# Step 5: Sign each entry
echo ""
echo "[5/6] Signing entries..."

sign_count=0
fail_count=0

for entry in "${ENTRIES[@]}"; do
    IFS=':' read -r line_num event_type event_id short_hash <<< "$entry"
    
    # Calculate array index (line_num is 1-indexed, arrays are 0-indexed)
    array_index=$((line_num - 1))
    
    echo ""
    echo "  Signing entry $((sign_count + 1))/8: ${event_type} (line ${line_num})"
    echo "    Event ID: ${event_id}"
    echo "    Hash: ${short_hash}..."
    
    # Extract the entry from chain.jsonl
    entry_file="${SIGNATURES_DIR}/entry_$(printf '%03d' $((sign_count + 1)))_${event_type}.json"
    
    # Use Python to extract the specific line (0-indexed array access)
    if ! "${VENV_BIN}/python" -c "
import json
with open('${CHAIN_FILE}') as f:
    lines = f.readlines()
    if ${array_index} < len(lines):
        entry = json.loads(lines[${array_index}])
        # Verify this is the right entry
        if entry.get('event_id') == '${event_id}' and entry.get('event_type') == '${event_type}':
            print(lines[${array_index}].strip())
            exit(0)
        else:
            print(f'ERROR: Entry mismatch. Expected ${event_id}/${event_type}', file=__import__('sys').stderr)
            exit(1)
    else:
        print(f'ERROR: Line ${line_num} out of range', file=__import__('sys').stderr)
        exit(1)
" > "${entry_file}" 2>/dev/null; then
        echo "    ERROR: Failed to extract entry"
        fail_count=$((fail_count + 1))
        continue
    fi
    
    # Sign the entry
    sig_file="${entry_file}.sig"
    if gpg --sign --armor --output "${sig_file}" --local-user "${KEY_ID}" "${entry_file}" 2>/dev/null; then
        echo "    SUCCESS: Signature created"
        sign_count=$((sign_count + 1))
    else
        echo "    ERROR: GPG signing failed"
        fail_count=$((fail_count + 1))
    fi
done

echo ""
echo "Signing complete: $sign_count succeeded, $fail_count failed"

# Step 6: Verify all signatures
echo ""
echo "[6/6] Verifying signatures..."

if [ "$sign_count" -gt 0 ]; then
    verification_count=0
    verification_fail=0
    
    for entry in "${ENTRIES[@]}"; do
        IFS=':' read -r line_num event_type event_id short_hash <<< "$entry"
        
        entry_file="${SIGNATURES_DIR}/entry_$(printf '%03d' $((verification_count + 1)))_${event_type}.json"
        sig_file="${entry_file}.sig"
        
        if [ -f "${sig_file}" ]; then
            if gpg --verify "${sig_file}" "${entry_file}" 2>/dev/null; then
                echo "  ${event_type}: VERIFIED"
                verification_count=$((verification_count + 1))
            else
                echo "  ${event_type}: VERIFICATION FAILED"
                verification_fail=$((verification_fail + 1))
            fi
        else
            echo "  ${event_type}: SIGNATURE FILE NOT FOUND"
            verification_fail=$((verification_fail + 1))
        fi
        
        # Stop after 8 entries
        if [ "$verification_count" -ge 8 ]; then
            break
        fi
    done
    
    echo ""
    echo "Verification complete: $verification_count verified, $verification_fail failed"
fi

# Summary
echo ""
echo "=========================================="
echo "Signing Ceremony Summary"
echo "=========================================="
echo "Entries signed: $sign_count / 8"
echo "Signatures verified: $verification_count / 8"
echo "Signature files location: ${SIGNATURES_DIR}"
echo ""
echo "Files created:"
ls -la "${SIGNATURES_DIR}"/*.sig 2>/dev/null || echo "  (no signature files found)"
echo ""
echo "=========================================="
echo "Next steps:"
echo "1. Review the signature files in ${SIGNATURES_DIR}"
echo "2. Export and share your public key if needed:"
echo "   gpg --armor --export ${KEY_ID} > founder_public_key.asc"
echo "3. Commit the signature files to the repository"
echo "4. Update the audit chain to record the signatures"
echo "=========================================="

# Exit with error if any signing failed
if [ "$fail_count" -gt 0 ]; then
    exit 1
fi

exit 0