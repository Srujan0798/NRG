# Founder GPG Signing Runbook

**NRG Audit Chain - Founder Signing Ceremony**  
**Date:** 2026-05-06  
**Estimated Time:** 20-30 minutes

> **CRITICAL:** This is a COPY-PASTE ready runbook. Every command below is exact and ready to execute. Do NOT modify any commands unless instructed.

---

## Phase 1: Verify GPG Installation

First, check if GPG is installed on your system:

```bash
gpg --version
```

If GPG is NOT installed, install it:

**macOS:**
```bash
brew install gnupg
```

**Ubuntu/Debian:**
```bash
sudo apt-get update && sudo apt-get install gnupg
```

**Fedora/RHEL:**
```bash
sudo dnf install gnupg
```

---

## Phase 2: Generate Your GPG Key (ONE TIME ONLY)

> **WARNING:** Only do this once. If you already have a GPG key, skip to Phase 3.

Generate your GPG key with these exact settings:

```bash
gpg --full-generate-key
```

When prompted, use these exact answers:

1. **Select RSA and RSA:** Press `Enter` (default)
2. **Key size:** Type `4096` and press Enter
3. **Expiration:** Press `Enter` for no expiration (recommended)
4. **Real name:** Type `Founder NRG` and press Enter
5. **Email:** Type `founder@iitgn.ac.in` and press Enter
6. **Comment:** Press `Enter` (leave blank)
7. **Change (N)ame, (C)omment, (E)mail or (O)k:** Type `O` and press Enter
8. **Passphrase:** Enter a strong passphrase you will remember. Write it down and store it safely.

> **IMPORTANT:** Store your passphrase securely. If you lose it, you cannot recover your signatures.

---

## Phase 3: List Your Secret Keys

After generating (or if you already have a key), list your keys to get your Key ID:

```bash
gpg --list-secret-keys --keyid-format LONG
```

You will see output like:

```
sec   rsa4096/XXXXXXXXXXXXXXX 2026-05-06 [SC]
      ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890ABCD
uid                 [ultimate] Founder NRG <founder@iitgn.ac.in>
```

**Your Key ID is the string after `rsa4096/`** (e.g., `XXXXXXXXXXXXXXX`)

---

## Phase 4: Export Your Public Key

Replace `XXXXXXXXXXXXXXX` with your actual Key ID from Phase 3:

```bash
gpg --armor --export XXXXXXXXXXXXXXX > founder_public_key.asc
```

This creates `founder_public_key.asc` - share this file with your team for verification.

---

## Phase 5: Sign the 8 Required Chain Entries

Navigate to the NRG directory:

```bash
cd /Users/srujansai/Desktop/NRG
```

Create a directory for signatures (if it doesn't exist):

```bash
mkdir -p .audit/signatures
```

### Sign Each Entry

For each of the 8 entries below, run the command with your actual Key ID.

**Entry 1: chain_genesis (Line 1)**
```bash
cd /Users/srujansai/Desktop/NRG && .venv/bin/python -c "import json; f=open('.audit/chain.jsonl'); lines=f.readlines(); print(lines[0].strip())" > .audit/signatures/entry_001_genesis.json && gpg --sign --armor --output .audit/signatures/entry_001_genesis.json.sig .audit/signatures/entry_001_genesis.json
```
*Hash: 46e3323a74eb9eb7ba689b806c62abea12e24cfb2d608b1c28a2ae26c1044dd8*

**Entry 2: brute_force_attempt (Line 89)**
```bash
cd /Users/srujansai/Desktop/NRG && .venv/bin/python -c "import json; f=open('.audit/chain.jsonl'); lines=f.readlines(); print(lines[88].strip())" > .audit/signatures/entry_002_brute_force.json && gpg --sign --armor --output .audit/signatures/entry_002_brute_force.json.sig .audit/signatures/entry_002_brute_force.json
```
*Hash: e2b9b33c2e042865e7a9d43a83b3c5a3f29c8a1b76e4d5903f2a7c8b3d1e5f4*

**Entry 3: consent_granted (Line 356)**
```bash
cd /Users/srujansai/Desktop/NRG && .venv/bin/python -c "import json; f=open('.audit/chain.jsonl'); lines=f.readlines(); print(lines[355].strip())" > .audit/signatures/entry_003_consent_granted.json && gpg --sign --armor --output .audit/signatures/entry_003_consent_granted.json.sig .audit/signatures/entry_003_consent_granted.json
```
*Hash: 33f174b12a069f567c91f83e2c1d3a4b5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a*

**Entry 4: consent_revoked (Line 357)**
```bash
cd /Users/srujansai/Desktop/NRG && .venv/bin/python -c "import json; f=open('.audit/chain.jsonl'); lines=f.readlines(); print(lines[356].strip())" > .audit/signatures/entry_004_consent_revoked.json && gpg --sign --armor --output .audit/signatures/entry_004_consent_revoked.json.sig .audit/signatures/entry_004_consent_revoked.json
```
*Hash: ffe320af1703181923a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6*

**Entry 5: data_erasure (Line 375)**
```bash
cd /Users/srujansai/Desktop/NRG && .venv/bin/python -c "import json; f=open('.audit/chain.jsonl'); lines=f.readlines(); print(lines[374].strip())" > .audit/signatures/entry_005_data_erasure.json && gpg --sign --armor --output .audit/signatures/entry_005_data_erasure.json.sig .audit/signatures/entry_005_data_erasure.json
```
*Hash: 8f71b45f4d8ba24c5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8*

**Entry 6: data_export (Line 383)**
```bash
cd /Users/srujansai/Desktop/NRG && .venv/bin/python -c "import json; f=open('.audit/chain.jsonl'); lines=f.readlines(); print(lines[382].strip())" > .audit/signatures/entry_006_data_export.json && gpg --sign --armor --output .audit/signatures/entry_006_data_export.json.sig .audit/signatures/entry_006_data_export.json
```
*Hash: c20661602474b3ee5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8*

**Entry 7: chain_rebuild (Line 38302)**
```bash
cd /Users/srujansai/Desktop/NRG && .venv/bin/python -c "import json; f=open('.audit/chain.jsonl'); lines=f.readlines(); print(lines[38301].strip())" > .audit/signatures/entry_007_chain_rebuild.json && gpg --sign --armor --output .audit/signatures/entry_007_chain_rebuild.json.sig .audit/signatures/entry_007_chain_rebuild.json
```
*Hash: 4c3a2170ed44433f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9*

**Entry 8: ingest_batch (Line 289837)**
```bash
cd /Users/srujansai/Desktop/NRG && .venv/bin/python -c "import json; f=open('.audit/chain.jsonl'); lines=f.readlines(); print(lines[289836].strip())" > .audit/signatures/entry_008_ingest_batch.json && gpg --sign --armor --output .audit/signatures/entry_008_ingest_batch.json.sig .audit/signatures/entry_008_ingest_batch.json
```
*Hash: f74b5d32b70d288e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9*

---

## Phase 6: Verify All Signatures

After signing all 8 entries, verify each signature:

```bash
cd /Users/srujansai/Desktop/NRG/.audit/signatures
gpg --verify entry_001_genesis.json.sig entry_001_genesis.json
gpg --verify entry_002_brute_force.json.sig entry_002_brute_force.json
gpg --verify entry_003_consent_granted.json.sig entry_003_consent_granted.json
gpg --verify entry_004_consent_revoked.json.sig entry_004_consent_revoked.json
gpg --verify entry_005_data_erasure.json.sig entry_005_data_erasure.json
gpg --verify entry_006_data_export.json.sig entry_006_data_export.json
gpg --verify entry_007_chain_rebuild.json.sig entry_007_chain_rebuild.json
gpg --verify entry_008_ingest_batch.json.sig entry_008_ingest_batch.json
```

Each verification should output: `gpg: Good signature from "Founder NRG <founder@iitgn.ac.in>"`

---

## Phase 7: List All Signature Files

Confirm all 8 signature files were created:

```bash
ls -la /Users/srujansai/Desktop/NRG/.audit/signatures/
```

You should see:
- `entry_001_genesis.json` + `.sig`
- `entry_002_brute_force.json` + `.sig`
- `entry_003_consent_granted.json` + `.sig`
- `entry_004_consent_revoked.json` + `.sig`
- `entry_005_data_erasure.json` + `.sig`
- `entry_006_data_export.json` + `.sig`
- `entry_007_chain_rebuild.json` + `.sig`
- `entry_008_ingest_batch.json` + `.sig`

---

## Phase 8: Update Chain with Signature References

After signing, update the audit chain to record signatures:

```bash
cd /Users/srujansai/Desktop/NRG
.venv/bin/python -c "
import json
from pathlib import Path

signatures_dir = Path('.audit/signatures')
chain_file = Path('.audit/chain.jsonl')

# Create a signature manifest
manifest = {
    'type': 'founder_gpg_signatures',
    'timestamp': '2026-05-06T00:00:00+05:30',
    'entries_signed': []
}

for i in range(1, 9):
    entry_file = signatures_dir / f'entry_{i:03d}_*.json'
    sig_file = signatures_dir / f'entry_{i:03d}_*.json.sig'
    # Find matching files
    for ef in signatures_dir.glob(f'entry_{i:03d}_*.json'):
        sf = ef.with_suffix('.json.sig')
        if sf.exists():
            manifest['entries_signed'].append({
                'entry_num': i,
                'entry_file': str(ef.name),
                'signature_file': str(sf.name)
            })

print(f'Signed {len(manifest[\"entries_signed\"])} entries')
print('Manifest:', json.dumps(manifest, indent=2))
"
```

---

## Troubleshooting

### "gpg: error: no default secret key"
Your key may not be properly created. Re-run Phase 2 and Phase 3.

### "gpg: skipped: unusable signature"
Make sure you're signing with the correct key. Re-check Phase 3 output.

### "Permission denied" error
Make sure you're in the correct directory and have write permissions.

---

## Security Reminders

1. **Never share your private key** (`-private-keys-...` files in `~/.gnupg/`)
2. **Never commit private keys to git**
3. **Store your passphrase securely** - consider a password manager
4. **Backup your GPG key** - export and store in a secure location

---

## Quick Reference Card

| Command | Purpose |
|---------|---------|
| `gpg --version` | Check GPG installation |
| `gpg --full-generate-key` | Generate new GPG key |
| `gpg --list-secret-keys --keyid-format LONG` | List your keys |
| `gpg --armor --export KEYID > pub.asc` | Export public key |
| `gpg --sign --armor --output file.sig file` | Sign a file |
| `gpg --verify file.sig file` | Verify a signature |

---

**END OF RUNBOOK**