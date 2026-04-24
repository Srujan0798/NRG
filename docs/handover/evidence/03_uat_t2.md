# NRG UAT — Tier 2 Government Liaison (Tier 2) — Step 3b

**Protocol**: #45 Eternal Seal
**Step**: 03_uat_t2
**Persona**: Government Ministry Liaison (Tier 2 — aggregated/anonymized data)
**Tester**: [Ministry Representative Name]
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

## Tier 2 Data Rules

- Data is **aggregated** — no individual researcher records
- Geographic resolution: state-level minimum (not institute-level)
- Financial data: **rounded to nearest lakh** — no precise figures
- PII: **ZERO** — no names, emails, phone numbers, Aadhaar, PAN
- Pre-publication data **hidden** until publicly released

---

## Suggested Tier 2 Queries

1. "Show me total PhD output by state for FY 2023-24"
2. "What is the national TRL distribution for clean energy?"
3. "Compare government funding between Karnataka vs Gujarat over 3 years"
4. "Which ministry's projects have highest commercialization rate?"
5. "Show me aggregate startup funding by sector across all IITs"
6. "What is the year-over-year growth in patents granted nationally?"
7. "Flag any institutes with >50% funding drop year-over-year"
8. "Show me the top 10 TRL Level 9 innovations nationally"
9. "What is the total seed funding deployed to startups in 2023-24?"
10. "Compare Capex vs operational expenditure across all institutes"

---

## Required Query Types (include at least 2 of each)

- [ ] Simple aggregation (state-level, ministry-level)
- [ ] Comparison query (compare X vs Y — state/ministry level)
- [ ] Gap analysis (national trends, year-over-year)
- [ ] Multi-hop synthesis (SQL + RAG — aggregated)
- [ ] Temporal RBAC (check visibility window for pre-publication data)

---

## PII Leak Check

After each query, run:
```bash
python -c "from src.security.gateway.prompt_sanitiser import prompt_sanitiser; print(prompt_sanitiser.check(response_text))"
```
Expected: **ZERO Indian PII** — Aadhaar, PAN, phone, email, names must not appear

---

## Audit Chain Verification

After session:
```bash
kubectl -n nrg exec deploy/api -- python -c "from src.audit import verify_chain; v, e, n = verify_chain(); print(f'Valid: {v}, Events: {n}, Errors: {e}')"
```
Expected: `True, [], N` where N ≥ event count from UAT session

---

## Gate

- 10/10 queries pass persona-appropriate validation (Tier 2 rules enforced)
- No PII leaks detected
- verify_chain() returns valid
- → Session PASS → signed by ministry liaison

## Signature

Ministry liaison GPG sign: `gpg --detach-sign 03_uat_t2.md`
→ `03_uat_t2.md.asc` stored in `docs/handover/signatures/`
