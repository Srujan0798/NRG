# NRG Handover — Signature Manifest

**Protocol**: #45 Eternal Seal — Step 6
**Status**: PENDING — Waiting for all 5 steps above to complete

---

## Required Signatures (8 files)

| # | File | Signer | Status |
|---|------|--------|--------|
| 1 | docs/handover/evidence/01_stage_up.json | DevOps | ⏳ Pending |
| 2 | docs/handover/evidence/02_load_report.md | DevOps | ⏳ Pending |
| 3 | docs/handover/evidence/03_uat_t1.md | Professor | ⏳ Pending |
| 4 | docs/handover/evidence/03_uat_t2.md | Ministry Rep | ⏳ Pending |
| 5 | docs/handover/evidence/03_uat_t3.md | Industry Partner | ⏳ Pending |
| 6 | docs/handover/evidence/04_demo.sha256 | Founder | ⏳ Pending |
| 7 | docs/handover/SECURITY_COMPLIANCE_ATTESTATION.md | Founder | ⏳ Pending |
| 8 | docs/handover/UAT_RESULTS.md | Professor | ⏳ Pending |

---

## Signing Commands

```bash
cd /Users/srujansai/Desktop/NRG

# Each signer runs (example for 01_stage_up.json):
gpg --detach-sign docs/handover/evidence/01_stage_up.json
# → produces: docs/handover/evidence/01_stage_up.json.asc

# Repeat for each file above
```

## Verification

```bash
# Check all .asc files exist
ls docs/handover/signatures/*.asc | wc -l
# Expected: 8

# Verify each signature
gpg --verify docs/handover/evidence/01_stage_up.json.asc docs/handover/evidence/01_stage_up.json
```

---

## Terminal Step: Git Tag

After all 8 signatures collected:

```bash
git tag -s v1.0.0-eternal \
  -m "NRG eternal completion — QB 6/6, 33/33 protocols, sovereign live.

Quality Bar: 6/6
- C1: DPDP Indian PII ✅
- C2: Per-user audit binding ✅
- C3: Multi-hop DAG planner ✅
- C4: P99<500ms @ 1000 concurrent ✅
- C5: Vector drift auto-retrain ✅
- C6: Schema allowlist egress ✅

Handover: 8/8 signatures present.
7 tail-items: ALL CLOSED.
Protocols: 33/33 COMPLETE."

git push nrg v1.0.0-eternal
```

## SHADOWING_LOG Creation

```bash
# Create day-0 entry
cat > docs/handover/SHADOWING_LOG.md << 'EOF'
# NRG Shadowing Log

## Day 0 — v1.0.0-eternal
**Date**: [TBD]
**Tag**: v1.0.0-eternal
**Chain Head**: [from 05_chain_seal.json]
**Signed By**: [Founder Name]

## 30/60/90 Day Cadence

| Checkpoint | Target Date | Status |
|-----------|-------------|--------|
| Day 30 | [Date+30] | ⏳ |
| Day 60 | [Date+60] | ⏳ |
| Day 90 | [Date+90] | ⏳ |

---
EOF
```
