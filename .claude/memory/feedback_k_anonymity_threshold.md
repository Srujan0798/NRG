---
name: k-anonymity threshold rejection for inference attacks
description: Tier filtering and column masking are insufficient against inference attacks where a narrowly-filtered query identifies a unique individual. Reject queries whose WHERE-clause cohort is < k=5; require operator override via audit-logged Tier 1 path.
type: feedback
---

LB-1 (tier-shape) and `feedback_db_layer_defence.md` (pg_anonymizer) protect against direct PII column access. Neither protects against an **inference attack** where a Tier 2/3 user uses a narrow `WHERE` clause to isolate a single individual:

> "Show me grant funding for the only female researcher aged 55 specialising in deep learning at IIT Manipur."

If the cohort matching that filter is one person, returning even non-PII fields (grant amount, project title) reveals personal financial data. Section 8 of DPDP 2023 explicitly bars this. `pg_anonymizer` masks Aadhaar but does not see the WHERE clause; the response-shape filter sees the result rows but does not measure cohort size.

**Required: a k-anonymity threshold check before returning ANY filtered result.**

- Default `k = 5` for Tier 2/3. Tier 1 sees a warning but is permitted.
- If `WHERE`-clause-filtered cohort < k, the engine refuses and returns: "Query result cohort is below the privacy-preserving threshold (k=5). Broaden the criteria or request operator review."
- Implementation: a verifier-node check that runs `SELECT count(*) FROM <derived_filter_subset>` BEFORE returning the requested aggregate; if < k, abort.
- Audit-log every threshold-rejection (`k_anonymity_block:tier3:cohort=1`). Operators can monitor for systematic probing.
- Tier 1 override path: if Tier 1 user explicitly affirms "I need this individually-identifiable result", the engine logs the consent + identity + reason and returns the result. Audit chain proves the trail.

**Why:** External reviewers all flagged differential-privacy concerns. The engineering complexity is small; the legal exposure if missed is large. Adding this check pre-emptively closes a class of attack the response-shape filter cannot see.

**How to apply:**
- New protocol when promoted: **LB-10 — K-Anonymity Threshold + Inference Attack Defence**. For now this entry is the canonical reference.
- Wires into the verifier node (`src/orchestration/nodes/verifier.py`). Add to LB-7 acceptance as a Phase 3 IMMORTALIZE bullet (anomaly detection's natural cousin).
- Tested by extending `tests/security/test_egress_allowlist.py` with k-anon cases: 1-row filter, 2-row, 4-row (all should block); 5-row (allowed).
- Cross-reference Risk #2 (PII leak) and the new Risk #29 (inference-attack via narrow WHERE) in the register.

**Source:** The Principal Auditor 2026-04-26 (D4 Q4). Promoted 2026-04-26.
