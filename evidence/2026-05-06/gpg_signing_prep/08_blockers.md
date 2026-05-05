# GPG Signing Ceremony - Blockers

**Date:** 2026-05-06  
**Task:** shishya_gpg_signing_ceremony_prep

## Status: PARTIAL - Waiting for Founder Action

The signing ceremony preparation is complete. All evidence files are created and verified. The signing script passes syntax checks. However, the actual GPG signing cannot proceed until the founder completes the following actions.

---

## Blockers

### BLOCKER 1: Founder GPG Key Generation (REQUIRED)

**Status:** BLOCKED  
**Action Required:** Founder must generate a GPG key

The agent is prohibited from generating the founder's GPG key. This is a founder-only action per the assignment constraints.

**What founder must do:**
1. Run `gpg --full-generate-key`
2. Use RSA 4096, no expiry
3. Name: "Founder NRG"
4. Email: founder@iitgn.ac.in
5. Store passphrase securely

**Estimated time:** 10-15 minutes

---

### BLOCKER 2: Founder GPG Signing (REQUIRED)

**Status:** BLOCKED  
**Action Required:** Founder must run the signing script or individual commands

The signing script (`06_signing_script.sh`) is ready to execute. Founder must run it.

**What founder must do:**
1. Navigate to `/Users/srujansai/Desktop/NRG`
2. Run `./evidence/2026-05-06/gpg_signing_prep/06_signing_script.sh`
3. If multiple keys exist, select the correct one when prompted

**Estimated time:** 5-10 minutes

---

### BLOCKER 3: Signature Verification (REQUIRED)

**Status:** BLOCKED  
**Action Required:** Founder must verify signatures after signing

After signing, founder must verify all 8 signatures to confirm the ceremony completed successfully.

**What founder must do:**
1. Run verification commands in Phase 6 of `05_founder_runbook.md`
2. Confirm all 8 signatures show "Good signature from 'Founder NRG <founder@iitgn.ac.in>'"

**Estimated time:** 2-3 minutes

---

## Pre-Signing Checklist (For Founder)

Before starting the signing ceremony, confirm:

- [ ] GPG is installed (`gpg --version` works)
- [ ] You have generated a GPG key (or have an existing one)
- [ ] You know your key ID (run `gpg --list-secret-keys --keyid-format LONG`)
- [ ] You have your passphrase available
- [ ] You are in the correct directory: `/Users/srujansai/Desktop/NRG`
- [ ] You have 30 minutes of uninterrupted time

---

## Files Ready for Founder

| File | Purpose | Ready? |
|------|---------|--------|
| `06_signing_script.sh` | Automated signing script | YES |
| `05_founder_runbook.md` | Step-by-step manual signing | YES |
| `04_entries_to_sign.md` | List of 8 entries to sign | YES |

---

## What Happens Next

1. Founder generates GPG key
2. Founder runs signing script
3. Script creates 8 signature files in `.audit/signatures/`
4. Founder verifies all signatures
5. Agent runs post-signing verification
6. Chain is marked as "founder signed"

---

## Dependencies

None - all preparation work is complete.

---

## Contact

For questions about the signing process, refer to:
- `05_founder_runbook.md` - detailed step-by-step guide
- `06_signing_script.sh` - automated signing script
- `.claude/skills/nrg-audit-chain/SKILL.md` - audit chain documentation