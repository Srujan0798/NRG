# External Audit Handling Rule

> **When an external audit contradicts an internal claim, the internal claim is WRONG until proven otherwise.**

---

## The Rule

```
External auditor says X is broken     → Assume X is broken
Internal report says X is 10/10       → Suspended until verified
External + Internal disagree          → External wins every time
```

**Why:** The external auditor has no incentive to flatter you. Their reputation depends on finding real gaps. Your internal report's 10/10 score depends on your own assessment, which is biased by sunk cost.

---

## The Process

### Step 1: Read Completely
Read the external audit end-to-end before defending anything. Every finding, every file reference, every line number.

### Step 2: Verify Independently
For every finding, run the verification yourself:

| Common Claim | Verification | Tool/Command |
|---|---|---|
| "Qdrant empty" | Check vector count | `curl /health` or Qdrant client |
| "90% errors at 100 users" | Re-run Locust | `locust -f tests/load/locustfile_c4.py` |
| "Table name not aliased" | Grep codebase | `grep -r long_name src/skills/text_to_sql/` |
| "7–12s cold latency" | Time cold query | `time curl -X POST /api/query/stream` |
| "Audit chain broken" | Direct verification | `python -c "from src.audit import verify_chain; print(verify_chain())"` |
| "Health endpoint lying" | Compare checks | `verify_chain()` vs `/health` output |

**Critical:** Use `verify_chain()` for audit checks, NOT `/health`. `/health` may auto-repair and hide root failures.

### Step 3: Classify

| Category | Action | Example |
|---|---|---|
| **REAL** | Add to BACKLOG.md, assign agent, close with evidence | "90% error rate" — re-run Locust, fix config, re-test |
| **FALSE** | Document counter-evidence, add to memory | "Qdrant empty" — but vectors=1800 |
| **OUTDATED** | Document when fixed and what commit | "59-byte table name" — fixed in 964c2bb |
| **PARTIAL** | Fix the real part, document the false part | "7–12s latency" — SSE exists but cold path still slow |

### Step 4: Rewrite Contradictory Reports
If an internal report (e.g., `NRG_50LAKH_DELIVERY_REPORT.md`) claims 10/10 while the external audit claims 6/10, the internal report must be:
- Rewritten to reflect reality, OR
- Removed and replaced with an honest assessment, OR
- Kept as a historical artifact with a clear header: `SUPERSEDED BY <external_audit>`

**Never let contradictory reports coexist without explanation.**

---

## Forbidden Vocab in External-Facing Docs

External-facing documents (reports, pitch decks, delivery documents) are the MOST likely place forbidden vocabulary leaks in. Before any external document is committed:

```bash
# Scan ALL .md files, including root directory
bash scripts/forbidden_vocab_check.sh
# If it fails, fix the document before any external party sees it
```

---

## Evidence Expiration for External Audits

| Audit Finding Type | Max Age Before Re-verify |
|---|---|
| Load test results | 7 days |
| Benchmark scores | 7 days |
| Security scan results | 14 days |
| Vector drift scores | 1 day |
| Audit chain status | 1 day |

**Rule:** If an external audit references evidence older than max age, the evidence is stale. Re-run the test and produce fresh evidence before responding to the audit.

---

## The Co-Work Audit Checklist

Before submitting any work to an external reviewer (co-work, IRPC, IndiaAI, ministry):

- [ ] `verify_chain()` returns `(True, [], N)` — not just `/health`
- [ ] `forbidden_vocab_check.sh` passes on ALL files including `.md`
- [ ] Load test evidence is < 7 days old
- [ ] Benchmark evidence is < 7 days old
- [ ] No contradictory internal reports exist in the repo
- [ ] All external audit findings from previous rounds are addressed in BACKLOG.md
