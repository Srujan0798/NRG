# GAP-H Closure Evidence — GPG Signature Workflow

**Date:** 2026-04-27
**GAP:** GAP-H — GPG signatures on 8 handover docs
**Status:** READY — Requires founder key ceremony (OPS)

## What's Ready

### 1. Signature Manifest (`docs/handover/signatures/SIGNATURE_MANIFEST.md`)

Complete with:
- 8 files requiring signatures
- Signer assignments (DevOps × 2, Professor × 2, Ministry Rep, Industry Partner, Founder × 2)
- Step-by-step `gpg --detach-sign` commands
- Verification commands
- Final git tag instructions (`v1.0.0-eternal`)

### 2. Files Requiring Signatures

| # | File | Signer |
|---|------|--------|
| 1 | `docs/handover/evidence/01_stage_up.json` | DevOps |
| 2 | `docs/handover/evidence/02_load_report.md` | DevOps |
| 3 | `docs/handover/evidence/03_uat_t1.md` | Professor |
| 4 | `docs/handover/evidence/03_uat_t2.md` | Ministry Rep |
| 5 | `docs/handover/evidence/03_uat_t3.md` | Industry Partner |
| 6 | `docs/handover/evidence/04_demo.sha256` | Founder |
| 7 | `docs/handover/SECURITY_COMPLIANCE_ATTESTATION.md` | Founder |
| 8 | `docs/handover/UAT_RESULTS.md` | Professor |

All 8 files are present and non-empty.

## Founder's Steps (5 minutes)

```bash
cd /Users/srujansai/Desktop/NRG

# 1. Verify all docs exist
ls docs/handover/evidence/01_stage_up.json
ls docs/handover/evidence/02_load_report.md
ls docs/handover/SECURITY_COMPLIANCE_ATTESTATION.md

# 2. Sign each doc
gpg --detach-sign docs/handover/evidence/04_demo.sha256
gpg --detach-sign docs/handover/SECURITY_COMPLIANCE_ATTESTATION.md

# 3. Verify
gpg --verify docs/handover/evidence/04_demo.sha256.asc docs/handover/evidence/04_demo.sha256
gpg --verify docs/handover/SECURITY_COMPLIANCE_ATTESTATION.md.asc docs/handover/SECURITY_COMPLIANCE_ATTESTATION.md

# 4. Tag the release (after all 8 signatures)
git tag -s v1.0.0-eternal -m "NRG eternal completion — QB 6/6, 33/33 protocols, sovereign live."
git push nrg v1.0.0-eternal
```

## OPS Acknowledgment

GAP-H is **ready to execute** — the workflow is documented, the files are present, the commands are clear. The founder needs to:
1. Have their GPG key ready (or generate one)
2. Run the signing ceremony (5 minutes)
3. Push the signed tag

**GAP-H STATUS: OPS — founder action required. All code/materials ready.**