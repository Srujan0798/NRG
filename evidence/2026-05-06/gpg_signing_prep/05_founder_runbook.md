# Founder GPG Signing Runbook

**Date:** 2026-05-06
**Goal:** sign 8 required audit-chain entries with founder-controlled GPG key.

Do not share the private key or passphrase. The agent must not generate or hold the founder key.

## 1. Install GPG

macOS:

```bash
brew install gnupg
gpg --version
```

Ubuntu:

```bash
sudo apt-get update
sudo apt-get install -y gnupg
gpg --version
```

## 2. Generate Founder Key

```bash
gpg --full-generate-key
```

Use these settings:

- Key type: RSA and RSA
- Key size: 4096
- Expiry: 0 / no expiry
- Name: Founder NRG
- Email: founder@iitgn.ac.in
- Passphrase: founder-controlled, stored offline

## 3. List Secret Keys

```bash
gpg --list-secret-keys --keyid-format LONG
```

Copy the key id after `rsa4096/`, for example `ABCDEF1234567890`.

## 4. Verify Audit Chain Before Signing

Run from repo root:

```bash
cd /Users/srujansai/Desktop/NRG
.venv/bin/python - <<'PY'
from src.audit import verify_chain
result = verify_chain()
valid = bool(result[0]) if isinstance(result, tuple) else bool(result)
print("VALID" if valid else f"CORRUPTED: {result}")
PY
wc -l .audit/chain.jsonl
cat .audit/genesis_hash.pin
```

Expected:

- `VALID`
- `609810 .audit/chain.jsonl` or higher if new audit events were appended after this prep
- genesis pin `46e3323a74eb9eb7ba689b806c62abea12e24cfb2d608b1c28a2ae26c1044dd8`

If chain verification fails, stop and do not sign.

## 5. Run Batch Signing Script

```bash
cd /Users/srujansai/Desktop/NRG
bash evidence/2026-05-06/gpg_signing_prep/06_signing_script.sh
```

The script will:

- check GPG is installed,
- list available secret keys,
- prompt for key id if needed,
- extract each required chain entry into `.audit/signatures/`,
- create detached ASCII-armored signatures,
- verify all 8 signatures.

## 6. Manual Signing Fallback

Use this only if the script cannot run:

```bash
mkdir -p .audit/signatures
sed -n '1p' .audit/chain.jsonl > .audit/signatures/entry_001_chain_genesis.json
gpg --armor --detach-sign --local-user <KEY_ID> --output .audit/signatures/entry_001_chain_genesis.json.asc .audit/signatures/entry_001_chain_genesis.json
gpg --verify .audit/signatures/entry_001_chain_genesis.json.asc .audit/signatures/entry_001_chain_genesis.json
```

Repeat for the 8 lines listed in `04_entries_to_sign.md`.

## 7. Export Public Key

```bash
gpg --armor --export <KEY_ID> > .audit/signatures/founder_public_key.asc
gpg --fingerprint <KEY_ID> > .audit/signatures/founder_key_fingerprint.txt
```

Commit only public key, fingerprints, extracted entry files, and detached signatures. Never commit the private key.

## 8. Final Verification

```bash
for sig in .audit/signatures/entry_*.json.asc; do
  entry="${sig%.asc}"
  gpg --verify "$sig" "$entry" || exit 1
done
echo "All founder signatures verified"
```
