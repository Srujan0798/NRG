#!/usr/bin/env bash
# ============================================================
# NRG GPG Signing - Founder One-Click Setup
# Run this file. Three commands. That's it.
# ============================================================

set -euo pipefail

EMAIL="founder@iitgn.ac.in"
NAME="Founder NRG"
REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"

echo ""
echo "============================================"
echo "  NRG GPG Signing Setup (Founder Only)"
echo "============================================"
echo ""

# ---- CHECK 1: GPG installed? ----
if command -v gpg >/dev/null 2>&1; then
  echo "[OK] GPG is installed:"
  gpg --version | head -1
else
  echo "[INSTALL] GPG is not installed."
  echo ""
  echo "Step 1 — Install GPG:"
  echo "----------------------------------------"
  echo "brew install gnupg"
  echo "----------------------------------------"
  echo ""
  echo "After installing GPG, re-run this script."
  exit 0
fi

# ---- CHECK 2: Key exists? ----
KEY_COUNT=$(gpg --list-secret-keys --keyid-format LONG 2>/dev/null | grep -c '^sec' || true)
if [[ "${KEY_COUNT}" -eq 0 ]]; then
  echo "[GENERATE] No GPG key found. You need to generate one."
  echo ""
  echo "Step 2 — Generate your GPG key (do this once):"
  echo "----------------------------------------"
  echo "gpg --full-generate-key"
  echo "----------------------------------------"
  echo ""
  echo "When prompted, use these exact values:"
  echo "  Key type    : RSA and RSA"
  echo "  Key size    : 4096"
  echo "  Expiry      : 0 (no expiry)"
  echo "  Real name   : ${NAME}"
  echo "  Email       : ${EMAIL}"
  echo "  Passphrase  : (choose a strong one, keep it offline)"
  echo ""
  echo "After generating the key, re-run this script."
  exit 0
fi

# ---- KEY SELECTED ----
KEY_ID=$(gpg --list-secret-keys --keyid-format LONG 2>/dev/null | awk -F'[/ ]+' '/^sec/{print $3; exit}')
echo "[KEY FOUND] Using: ${KEY_ID}"

echo ""
echo "============================================"
echo "  3 COMMANDS TO SIGN 8 ENTRIES"
echo "============================================"
echo ""
echo "Command 1 — Export your public key:"
echo "----------------------------------------"
echo "gpg --armor --export ${KEY_ID} > ${REPO_ROOT}/.audit/signatures/founder_public_key.asc"
echo "----------------------------------------"
echo ""
echo "Command 2 — Run the signing ceremony:"
echo "----------------------------------------"
echo "cd ${REPO_ROOT} && bash evidence/2026-05-06/gpg_signing_prep/06_signing_script.sh"
echo "----------------------------------------"
echo ""
echo "Command 3 — Verify all signatures:"
echo "----------------------------------------"
echo "for sig in ${REPO_ROOT}/.audit/signatures/entry_*.json.asc; do gpg --verify \"\$sig\" \"\${sig%.asc}\" || exit 1; done && echo 'ALL SIGNATURES VERIFIED'"
echo "----------------------------------------"
echo ""
echo "Paste and run each command in order."
echo "Script will auto-select your only key (${KEY_ID})."
