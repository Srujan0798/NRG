# NRG GPG Signing — Quick Start (Founder)

**Date:** 2026-05-06
**Purpose:** Sign 8 audit-chain milestone entries with your GPG key.

---

## Three Commands

Run these from the repo root:

### 1. Export your public key
```bash
gpg --armor --export <YOUR_KEY_ID> > .audit/signatures/founder_public_key.asc
```
Find `<YOUR_KEY_ID>` by running: `gpg --list-secret-keys --keyid-format LONG`
Copy the 16-char ID after `rsa4096/` (e.g. `ABCDEF1234567890`).

### 2. Run the signing ceremony
```bash
bash evidence/2026-05-06/gpg_signing_prep/06_signing_script.sh
```
This creates 8 detached `.asc` signatures in `.audit/signatures/`.

### 3. Verify all signatures
```bash
for sig in .audit/signatures/entry_*.json.asc; do gpg --verify "$sig" "${sig%.asc}" || exit 1; done && echo 'ALL SIGNATURES VERIFIED'
```

---

## Prerequisites (if not already done)

### Install GPG (macOS)
```bash
brew install gnupg
```

### Generate your key (once only)
```bash
gpg --full-generate-key
```
Use: RSA and RSA · 4096 bits · no expiry · `Founder NRG` · `founder@iitgn.ac.in`

---

## What's being signed

| # | Event | Line |
|---|-------|-----:|
| 1 | chain_genesis | 1 |
| 2 | brute_force_attempt | 89 |
| 3 | consent_granted | 356 |
| 4 | consent_revoked | 357 |
| 5 | data_erasure | 375 |
| 6 | data_export | 383 |
| 7 | chain_rebuild | 38,302 |
| 8 | ingest_batch | 289,837 |

Output goes to `.audit/signatures/entry_001_chain_genesis.json.asc` through `entry_008_ingest_batch.json.asc`.

---

## Verify chain before signing

```bash
.venv/bin/python -c "from src.audit import verify_chain; r=verify_chain(); print('VALID' if r else r)"
```

Expected output: `VALID`

If you see anything else, stop and do not sign.
