# NRG Handover Package — Master Index

> **Protocol #44 — THE HANDOVER PACKAGE**
> **Version:** 1.0  
> **Date:** 2026-04-24  
> **Classification:** IIT-GN Internal → Ministry Handoff  
> **Owner:** NRG Development Team  

---

## Purpose

A product that only its builders can operate is NOT a product — it's a liability.  
On the day we hand NRG to IIT-GN, they must be able to:

- ✅ Boot it
- ✅ Query it  
- ✅ Operate it
- ✅ Audit it
- ✅ Scale it
- ✅ Recover from disaster
- ✅ Pitch it to the ministry

**All WITHOUT calling us.**

---

## The 8 Handover Artifacts

| # | Document | Purpose | Audience |
|---|----------|---------|----------|
| 1 | **SYSTEM_OVERVIEW.md** | 10-page narrative for non-engineers | Ministry, IIT-GN leadership |
| 2 | **ARCHITECTURE.md** | Technical architecture with diagrams | IIT-GN ops team, NIC engineers |
| 3 | **API_REFERENCE.md** | Human-edited API docs with examples | Developers integrating with NRG |
| 4 | **OPERATIONS_RUNBOOK.md** | Day-2 ops: boot, backup, rotation, incidents | Ops team, on-call engineers |
| 5 | **SECURITY_COMPLIANCE_ATTESTATION.md** | QB 6/6 evidence, DPDP mapping, data flow | Security auditors, MeitY |
| 6 | **DATA_INTAKE_PROTOCOL.md** | SFTP + GPG + HMAC intake handshake | Data team, NIC intake operators |
| 7 | **UAT_RESULTS.md** | Test template for UAT session | UAT participants (professor, ministry, industry) |
| 8 | **README.md** | This file — master index | All readers |

---

## Phase 1: Fortify (Artifacts 1–8)

```
docs/handover/
├── README.md                          ← You are here
├── SYSTEM_OVERVIEW.md                 ← Artifact 1
├── ARCHITECTURE.md                    ← Artifact 2
├── API_REFERENCE.md                   ← Artifact 3
├── OPERATIONS_RUNBOOK.md             ← Artifact 4
├── SECURITY_COMPLIANCE_ATTESTATION.md ← Artifact 5
├── DATA_INTAKE_PROTOCOL.md            ← Artifact 6
└── UAT_RESULTS.md                    ← Artifact 7
```

---

## Phase 2: Elevate

| Deliverable | Status | Location |
|-------------|--------|----------|
| Pitch Deck (20 slides) | Pending | `pitch/NRG_PITCH_DECK.pdf` |
| Demo Video (3 min) | Pending | `pitch/NRG_DEMO.mp4` |
| UAT Session (1 hour) | Pending | Scheduled separately |

---

## Phase 3: Immortalize — Shadowing Timeline

| Phase | Duration | Ownership | NRG Team Role |
|-------|----------|-----------|---------------|
| **30-day shadowing** | Days 1–30 | NRG + IIT-GN ops together | Train, observe, refine |
| **60-day handover** | Days 31–90 | IIT-GN ops runs solo | On-call for P0 only |
| **90-day independence** | Day 91+ | IIT-GN owns completely | Retired |

---

## Quick Reference for IIT-GN Ops

```bash
# Boot the system
cd /opt/nrg && docker-compose up -d

# Check health
curl http://localhost:8000/health/all

# View audit chain
curl http://localhost:8000/audit/verify

# Rotate secrets (see OPERATIONS_RUNBOOK.md)
./scripts/rotate_secrets.sh

# Emergency contacts
#   Tech Lead:  +91-XXXXX-XXXXX
#   Security:   security@iitgn.ac.in
#   MeitY LIaison: meity@iitgn.ac.in
```

---

## Dependencies (Must Be Resolved Before Handover)

| Ticket | Description | Status |
|--------|-------------|--------|
| #41 | Quality Bar 6/6 score | Must pass |
| #42 | Frontend complete | Must pass |
| #43 | Sovereign deploy ready | Must pass |
| #19 | All tests green | Must pass |
| #20 | Dhairya benchmark ≥85% | Must pass |

---

## Sign-Off Checklist

| Document | Founder Sign-Off | Review Date |
|----------|-----------------|-------------|
| SYSTEM_OVERVIEW.md | ☐ | |
| ARCHITECTURE.md | ☐ | |
| API_REFERENCE.md | ☐ | |
| OPERATIONS_RUNBOOK.md | ☐ | |
| SECURITY_COMPLIANCE_ATTESTATION.md | ☐ | |
| DATA_INTAKE_PROTOCOL.md | ☐ | |
| UAT_RESULTS.md | ☐ | |

---

*Last updated: 2026-04-24*  
*Protocol #44 — THE HANDOVER PACKAGE*  
*NRG Development Team — signing off*