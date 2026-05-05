# Professor Audit v2 — Executive Summary

**Date:** 2026-05-06
**Auditor:** Professor's Senior Assistant, IIT Gandhinagar
**Student Claim:** Complete & excellent → 1cr funding
**Actual Score:** **4 / 10**

---

## 10-Dimension Scorecard

| # | Dimension | Score | Status | Key Evidence |
|---|-----------|-------|--------|-------------|
| 1 | Deployed Infrastructure | **0/10** | FAIL | No URL. Ports 8000/8001 unreachable. |
| 2 | SQL Quality | **8/10** | PASS | Dhairya 43/43 (100%). Killer queries SQL correct. |
| 3 | Performance / C4 SLO | **1/10** | FAIL | P99 4500ms (target <500ms). C5 timeout. |
| 4 | Frontend Quality | **2/10** | FAIL | Bundle WORSENED: 318KB → 476KB. |
| 5 | Security / Secrets | **5/10** | PARTIAL | DPDP/egress pass. 286 leaks purged. Rotation unknown. |
| 6 | Audit Chain | **2/10** | FAIL | 603,460 entries valid. 0/8 GPG signatures. |
| 7 | Killer Queries | **3/10** | FAIL | All 3 return `needs_clarification` (0.05 confidence). |
| 8 | CI/CD Pipeline | **4/10** | PARTIAL | 4 workflows exist. Never deployed. GHCR not AWS. |
| 9 | Workflow / Documentation | **9/10** | PASS | Hybrid format, validator, contradictions purged. |
| 10 | Code Completeness | **5/10** | UNKNOWN | Dhairya passes. Full traceability not audited. |

**Total: 39/100 = 3.9/10 → rounded to 4/10**

---

## Verdict

- **Show-ready:** NO
- **Production-ready:** NO
- **1 crore fundable:** NO
- **Realistic effort to fundable:** 2-3 weeks + ₹5-10L

---

## Top 3 Blockers

1. **No deployed URL** — cannot demonstrate to professor
2. **Killer queries fail live** — pipeline returns `needs_clarification` instead of answers
3. **C4 P99 4500ms** — 9x over target

---

## What Improved (Genuine)

- SQL quality: 43/43 Dhairya (up from 41%)
- Workflow: hybrid format, validator, contradiction purge
- Schema: 58 tables complete

## What Worsened

- Frontend bundle: 318KB → 476KB (failed optimization)
- Killer queries: discovered `needs_clarification` failure on live API
