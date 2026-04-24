# NRG UAT — Tier 3 Researcher (Professor) — Step 3

**Protocol**: #45 Eternal Seal
**Step**: 03_uat_t1
**Persona**: Industry R&D Executive (Tier 3)
**Tester**: [Industry Partner Name]
**Date**: [UAT Date]
**Duration**: 1 hour, 10 queries

---

## Test Matrix

| # | Query | Expected Behavior | Observed | PII Check | Latency | Citations | PASS/FAIL |
|---|-------|-----------------|----------|-----------|---------|-----------|-----------|
| 1 | [Query text] | [Expected response type] | [Observed] | ☐ Safe | [ms] | ☐ Yes | ☐ |
| 2 | | | | | | | |
| 3 | | | | | | | |
| 4 | | | | | | | |
| 5 | | | | | | | |
| 6 | | | | | | | |
| 7 | | | | | | | |
| 8 | | | | | | | |
| 9 | | | | | | | |
| 10 | | | | | | | |

---

## Required Query Types (include at least 2 of each)

- [ ] Simple lookup (list/find)
- [ ] Comparison query (compare X vs Y)
- [ ] Gap analysis (identify trends)
- [ ] Multi-hop synthesis (combine SQL + RAG)
- [ ] Temporal RBAC (check visibility window)

---

## PII Leak Check

Run each query through:
```bash
python -c "from src.security.gateway.prompt_sanitiser import prompt_sanitiser; print(prompt_sanitiser.check('QUERY'))
```

Expected: No Indian PII (Aadhaar, PAN, phone, email) in response

---

## Audit Chain Verification

After each session:
```bash
python -c "from src.audit import verify_chain; v, e, n = verify_chain(); print(f'Valid: {v}, Events: {n}, Errors: {e}')"
```

Expected: `True, [], N` where N ≥ event count from UAT session

---

## Gate

- 10/10 queries pass persona-appropriate validation
- No PII leaks detected
- verify_chain() returns valid
- → Session PASS → UAT_T1.md signed by professor

## Signature

Professor GPG sign: `gpg --detach-sign 03_uat_t1.md`
→ `03_uat_t1.md.asc` stored in `docs/handover/signatures/`
