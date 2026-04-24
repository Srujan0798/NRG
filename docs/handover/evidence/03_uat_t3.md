# NRG UAT — Tier 3 Industry Partner (Tier 3) — Step 3c

**Protocol**: #45 Eternal Seal
**Step**: 03_uat_t3
**Persona**: Industry R&D Executive (Tier 3 — fully anonymized, no individual records)
**Tester**: [Industry Partner Name]
**Date**: [UAT Date]
**Duration**: 1 hour, 10 queries

---

## Test Matrix

| # | Query | Expected Behavior | Observed | PII Check | Latency | PASS/FAIL |
|---|-------|-----------------|----------|-----------|---------|-----------|
| 1 | [Query text] | [Expected response type] | [Observed] | ☐ Safe | [ms] | ☐ |
| 2 | | | | | | |
| 3 | | | | | | |
| 4 | | | | | | |
| 5 | | | | | | |
| 6 | | | | | | |
| 7 | | | | | | |
| 8 | | | | | | |
| 9 | | | | | | |
| 10 | | | | | | |

---

## Tier 3 Data Rules

- Data is **fully anonymized** — no individual researcher, institute, or project names
- Institute labels replaced with anonymized codes (Tier3_001, Tier3_002, etc.)
- Financial data: **rounded to nearest Crore** — no precise figures
- **No direct institute identifiers** — only categories/clusters
- PII: **ABSOLUTE ZERO** — even aggregated PII is redacted
- Grant amounts: `sum_grant_received`, `avg_grant_received` only — raw `grant_received` **BLOCKED**

---

## Suggested Tier 3 Queries

1. "Show me the anonymized institute cluster with highest patent output in the last 3 years"
2. "What is the anonymized TRL pipeline distribution for clean energy sector?"
3. "Compare anonymized funding efficiency across industry-relevant sectors"
4. "Which anonymized institute cluster shows best cost-per-patent ratio?"
5. "Show me the anonymized year-over-year growth in publications for Tier 3 clusters"
6. "What is the national aggregate of TRL Level 8+ commercialization?"
7. "Flag anonymized institute clusters with >50% funding drop year-over-year"
8. "Show me the top 10 anonymized research areas by publication count"
9. "What is the aggregate startup ecosystem metric across anonymized clusters?"
10. "Compare anonymized Capex vs innovation output efficiency"

---

## Egress Allowlist Verification

Tier 3 queries must only use columns from the Tier 3 allowlist. Verify:
```bash
kubectl -n nrg exec deploy/api -- python -c "
from src.security.egress_allowlist import EgressGuard
guard = EgressGuard()
blocked = guard.check_query('YOUR_QUERY_HERE')
print(f'Blocked: {blocked}')
"
```
Expected: No block OR documented Tier 3 override

---

## Required Query Types (include at least 2 of each)

- [ ] Simple aggregation (anonymized cluster level)
- [ ] Comparison query (anonymized clusters vs sectors)
- [ ] Gap analysis (efficiency metrics)
- [ ] Multi-hop synthesis (SQL + RAG — anonymized)
- [ ] Temporal RBAC (check visibility window)

---

## PII Leak Check (Strictest — Tier 3)

After each query, run:
```bash
python -c "from src.security.gateway.prompt_sanitiser import prompt_sanitiser; print(prompt_sanitiser.check(response_text))"
```
Expected: **ZERO** — Tier 3 has strictest PII requirements. Even anonymized names must not appear.

---

## Audit Chain Verification

After session:
```bash
kubectl -n nrg exec deploy/api -- python -c "from src.audit import verify_chain; v, e, n = verify_chain(); print(f'Valid: {v}, Events: {n}, Errors: {e}')"
```
Expected: `True, [], N` where N ≥ event count from UAT session

---

## Gate

- 10/10 queries pass persona-appropriate validation (Tier 3 rules enforced)
- No PII leaks detected
- verify_chain() returns valid
- Egress allowlist not bypassed
- → Session PASS → signed by industry partner

## Signature

Industry partner GPG sign: `gpg --detach-sign 03_uat_t3.md`
→ `03_uat_t3.md.asc` stored in `docs/handover/signatures/`
