PROFESSOR'S ASSISTANT AUDIT REPORT – NRG National Research Graph
Date: 2026-05-06
Student Claim: Complete & excellent → 1cr funding requested
My mandate: Brutal honesty before any funding decision

---

# 1. TRUTH REPORT

| What the student claims | What the evidence actually shows |
|------------------------|----------------------------------|
| "Everything is complete and in excellent state" | 4/6 Quality Bar constraints pass. C4 P99 is 4500ms (9x over target). Killer queries all FAILED. Bundle got WORSE. |
| "All Text-to-SQL fixes are fixed in production" | Dhairya 43/43 PASS — genuine improvement. But killer queries LIVE all FAILED with `needs_clarification` (confidence 0.05). |
| "Main flow works perfectly for Tier 1/2/3" | No deployed URL exists. Cannot verify in browser. TestClient passes but live API fails killer queries. |
| "Frontend is zero-flaw" | Bundle INCREASED from 318KB to 476KB. Assignment made it WORSE. No deployed build to inspect. |
| "Backend is secure" | DPDP, egress, audit binding all pass locally. But 286 secrets were purged from history — live status unknown. |
| "Audit chain survives restart" | Chain is 603,460 entries and valid. But 0/8 founder GPG signatures. Chain is legally unsigned. |
| "Evidence package is ready" | 523 evidence files exist (May 5+6). But C4 optimization only has baseline (no fix). Bundle diet has failure evidence. |

---

# 2. HONEST 200-300 WORD ASSESSMENT

NRG is **not production software**. It is a locally-functional research prototype with severe gaps between "tests pass in isolation" and "works under load with real data."

The student has made **genuine improvements** in SQL quality (Dhairya 43/43, up from 41%) and workflow discipline (hybrid format, validator, contradiction purge). These are real.

But the **product fundamentals are broken**:
- Performance: P99 is 4500ms. The target is 500ms. This is not a tweak — it is a 9x gap.
- Killer queries: All 3 fail on live API with `needs_clarification` (confidence 0.05). The pipeline cannot answer them.
- Frontend: Bundle got WORSE (318KB → 476KB) after an optimization attempt.
- Data: Core killer-query tables in PostgreSQL are empty. Seed data exists in SQLite but was never migrated.
- Deployment: No staging URL. No successful deploy ever. CI/CD has never run on real infrastructure.
- Security: 286 secrets were in git history. Purged but rotation status unknown.
- Audit chain: 603,460 entries, 0 founder signatures.

The student is **overclaiming by a wide margin**. "Complete and excellent" is false. "Ready for 1 crore" is false. What exists is a promising v0.7 prototype with a well-organized workflow system. The workflow system is arguably more mature than the product itself.

---

# 3. TECHNICAL AUDIT CHECKLIST

| Item | Status | Evidence | Notes |
|------|--------|----------|-------|
| Text-to-SQL pipeline correctness | PASS | `evidence/2026-05-05/dhairya_regression_full/` — 43/43 | Dhairya benchmark passes. But live killer queries FAIL. |
| Schema parity (18 vs 58 tables) | PASS | `db_struct.sql` — 58 tables, 2 TRL views | Schema is complete. |
| RBAC at API layer | UNKNOWN | `src/auth/rbac.py` exists | Not tested live with different tier tokens. |
| Tier 3 zero-PII guarantee | UNKNOWN | `tests/security/test_pii_compliance.py` passes locally | Not verified on live deployed build. |
| Audit chain survives restart | PASS | `verify_chain()` returns valid | 603,460 entries. Valid. |
| HMAC signing | UNKNOWN | Code exists in `src/audit/` | Not verified with live signing. |
| DPDP compliance | PASS | C1: 10/10 tests pass | Local tests only. |
| Connection pooling | UNKNOWN | `docker-compose.yml` has pgbouncer | Not load-tested. |
| Async handlers (no sync I/O) | UNKNOWN | `src/api/main.py` | Not profiled. |
| Error handling (no raw tracebacks) | UNKNOWN | Middleware exists | Not adversarially tested. |
| Query result caching | UNKNOWN | Redis exists in compose | Not verified. |
| Multi-hop planner | PASS | C3: 31/31 tests pass | DAG planner works. |
| Vector drift detection | FAIL | C5: timeout after 120s | Qdrant not running or unreachable. |
| Egress allowlist | PASS | C6: 35/35 tests pass | Egress guard works. |

---

# 4. USER EXPERIENCE AUDIT

| Question | Answer | Evidence |
|----------|--------|----------|
| Can I access the app without SSH tunneling? | NO | No deployed URL. `CURRENT_STATE.md` §Deployed URLs: all BLOCKED. |
| Does login work with institutional SSO? | UNKNOWN | No deployed build to test. |
| Can I select my role? | UNKNOWN | No deployed build to test. |
| Can I submit a query and get a verified answer? | NO (live) | Killer queries all return `needs_clarification` on live API. |
| Are tables/graphs rendered or raw JSON? | UNKNOWN | No deployed build. |
| Are citations present and clickable? | UNKNOWN | No deployed build. |
| Is there audit proof I can download? | UNKNOWN | No deployed build. |
| Does the export function work? | UNKNOWN | No deployed build. |
| Are there console errors? | UNKNOWN | No deployed build. Local build passes. |
| Does it work on mobile? | UNKNOWN | No deployed build. |
| Is it accessible (WCAG 2.1 AA)? | UNKNOWN | No deployed build. No a11y audit evidence. |

---

# 5. TEN ADVERSARIAL QUESTIONS + THREE KILLER QUERIES

## Adversarial Questions
1. **Where is the deployed URL?** There is none. The student claims "complete" but cannot show a browser-accessible application.
2. **Why does P99 latency exceed the target by 9x?** 4500ms vs 500ms. This is not a minor gap.
3. **Why did the bundle optimization make things WORSE?** 318KB → 476KB. The "fix" increased size by 50%.
4. **Why are killer-query tables empty in PostgreSQL?** Seed data exists in SQLite but was never migrated. Basic data hygiene failure.
5. **Why do all 3 killer queries return `needs_clarification` with 0.05 confidence?** The pipeline cannot answer its own benchmark questions.
6. **Where are the 8 founder GPG signatures?** 603,460 audit entries, zero signatures. Legally unverifiable.
7. **Has the deploy workflow ever succeeded on real infrastructure?** No evidence exists.
8. **Why does vector drift detection timeout?** C5 fails because Qdrant is not running.
9. **Where is the credential rotation evidence?** 286 secrets were purged. Are any live? No plan has been executed.
10. **Is the workflow more mature than the product?** Yes. The hybrid format, validator, and assignment system are well-built. The product itself is not.

## Killer Query Results

| Query | Status | Generated SQL | Latency | Rows |
|-------|--------|---------------|---------|------|
| K-Q1 (TRL IIT Madras) | **FAIL** | Not captured | N/A | 0 |
| K-Q2 (cost-per-patent) | **FAIL** | `needs_clarification` | N/A | 0 |
| K-Q3 (grant drop + patent rise) | **FAIL** | `needs_clarification` | N/A | 0 |

All 3 failed with `answer_confidence: 'needs_clarification', answer_confidence_score: 0.05`.

---

# 6. RISK MAP (15 Risks)

| # | Risk | Probability | Impact | Prevention | Recovery |
|---|------|-------------|--------|------------|----------|
| 1 | P99 never reaches <500ms | High | Critical | Profile embedder, add async cache, connection pool | Accept higher latency or redesign hot path |
| 2 | Killer queries fail in front of professor | High | Critical | Seed PostgreSQL with real data, fix pipeline | Pre-run demo with known-good queries |
| 3 | No deployed URL at funding meeting | High | Critical | Create AWS account, deploy immediately | Run local demo via screen share |
| 4 | Bundle keeps growing | Medium | High | Proper code splitting, tree-shaking | Accept larger bundle if gzip acceptable |
| 5 | Credential rotation not done | Medium | Critical | Execute rotation plan | Document rotation timeline |
| 6 | GPG signing never happens | Medium | High | Generate key, run signing script | Accept unsigned chain (legal risk) |
| 7 | Qdrant drift detection broken | Medium | Medium | Fix Qdrant startup, timeout config | Manual drift checks |
| 8 | CI/CD deploy fails on first real run | High | High | Test deploy to staging first | Manual deployment fallback |
| 9 | Professor asks for mobile — it breaks | Medium | Medium | Test responsive design | Claim desktop-first MVP |
| 10 | Audit chain questioned in legal review | Medium | Critical | Sign chain, document integrity | Rebuild chain with signatures |
| 11 | Data seeding gap discovered mid-demo | High | Critical | Migrate SQLite seed to PostgreSQL | Pre-load demo data |
| 12 | Frontend console errors on deployed build | Medium | Medium | Build and test production bundle | Fix errors before deploy |
| 13 | RBAC bypass found by adversarial tester | Low | Critical | Penetration test API | Patch and re-audit |
| 14 | DPDP violation on live data | Low | Critical | Verify PII detection on real dataset | Legal review and remediation |
| 15 | Workflow becomes bottleneck (too many assignments) | Low | Medium | Consolidate assignments, prioritize | Reduce parallel work |

---

# 7. GAP FIX PROTOCOL

| Gap Name | Location | Root Cause | Fix Required | Test to Prove | Effort | Blocks 1cr? |
|----------|----------|------------|--------------|---------------|--------|-------------|
| P99 4500ms | `src/api/main.py`, embedder | Synchronous embedder call blocks async handlers | Make embedder async or add caching layer | `quality_bar_scorecard.py` P99 < 500ms | 3-5 days | YES |
| Killer queries return `needs_clarification` | `src/skills/text_to_sql/` | Pipeline cannot answer complex multi-table queries with live data | Fix query planner, seed PostgreSQL with data | `test_three_killer_queries.py` all PASS live | 2-3 days | YES |
| Empty PostgreSQL tables | `data/nrg_research.db` → PostgreSQL | Seed data in SQLite, never migrated to PostgreSQL | Write migration script, run seed | Killer queries return ≥1 row | 1 day | YES |
| Bundle 476KB | `frontend/vite.config.ts` | Lazy-loading attempt backfired | Revert lazy-load, try manualChunk in vite.config.ts | `npm run build` largest chunk < 250KB | 1-2 days | PARTIAL |
| No deployed URL | AWS/GCP | No cloud account provisioned | Create account, deploy to staging | `curl` staging URL returns 200 | 1-2 days | YES |
| 0 GPG signatures | `.audit/chain.jsonl` | Founder has not generated key | Generate key, run signing script | 8 signatures present | 2 hours | PARTIAL |
| C5 vector drift timeout | `scripts/vector_drift_check.py` | Qdrant not running | Fix Qdrant startup in compose | `vector_drift_check.py` exits 0 | 1 day | PARTIAL |
| Credential rotation unknown | Git history | 286 secrets purged, live status unknown | Execute rotation plan | Scanner shows 0 findings + plan approved | 2-3 days | PARTIAL |
| CI/CD never deployed | `.github/workflows/deploy.yml` | No real infrastructure to deploy to | Deploy to staging, verify pipeline | GH Actions shows green deploy | 1-2 days | PARTIAL |
| No mobile testing | `frontend/src/` | No responsive testing evidence | Test on mobile viewport | Screenshots on 3 screen sizes | 1 day | NO |

---

# 8. FINAL VERDICT

- **Overall readiness:** **4 / 10**
- **Show-ready right now:** **NO**
- **Production-ready right now:** **NO**
- **If NO, the 3 things that must happen first:**
  1. **Deploy to staging** — get a live URL that the professor can open
  2. **Fix killer queries on live API** — they must return real answers with ≥1 row
  3. **Fix C4 P99** — must drop from 4500ms to <500ms
- **Biggest single risk:** Professor opens the app and killer queries return "I don't know" (needs_clarification)
- **Most impressive thing:** Dhairya SQL benchmark 43/43 pass (100%) — up from 41%
- **Most embarrassing likely failure:** Bundle optimization made the frontend 50% larger

---

# 9. FUNDING DECISION

- **Would YOU approve 1 crore right now?** **NO**
- **Exact justification:** No deployed URL. No working killer queries on live API. P99 is 9x over target. Bundle got worse. 0 GPG signatures. The product is a v0.7 prototype with excellent workflow hygiene. Workflow does not equal product.
- **Realistic remaining effort:**
  - Time: **2-3 weeks of focused work**
  - Steps: Deploy → Fix killer queries → Fix C4 → Sign audit chain → Rotate credentials → Mobile test → Run Professor Audit again
  - Cost to complete: ~₹5-10L (developer time, cloud infra, security audit)

---

# 10. HANDOVER READINESS CHECKLIST

- [ ] README.md updated — UNKNOWN
- [ ] API docs complete — UNKNOWN
- [ ] Deployment guide exists — IN PROGRESS (`deployment_prep` assigned)
- [ ] Runbook exists — UNKNOWN
- [ ] Evidence package committed — PARTIAL (523 files, some incomplete)
- [ ] All 6 Quality Bar constraints pass — **NO** (4/6)
- [ ] Security scan clean — **NO** (rotation not done)
- [ ] Audit chain signed — **NO** (0/8)
- [ ] Staging URL live — **NO**
- [ ] Professor walkthrough script exists — **NO**
- [ ] Screenshot gallery exists — **NO**
- [ ] Video recording exists — **NO**
- [ ] Handover document signed — **NO**

**Missing: 9 of 13 artifacts.**

---

# 11. WORKFLOW EFFICIENCY & AGENTIC LOOP ANALYSIS

| Question | Answer |
|----------|--------|
| Are assignments actually getting executed? | **PARTIAL**. Dhairya regression PASSED. Killer queries live FAILED. Bundle diet FAILED. C4 optimization IN PROGRESS (only baseline). Credential rotation, GPG prep, deployment prep, CI/CD validation: NO EVIDENCE YET. |
| Is hybrid format producing better output? | **YES**. Assignments are clearer, more self-contained. But quality of execution varies. |
| Are Stop Rules preventing infinite loops? | **YES**. No evidence of infinite loops in any assignment. |
| Are Constraints preventing scope creep? | **MIXED**. Bundle diet constraint "do not remove features" was followed, but the fix made things worse. |
| Is evidence actually being committed? | **YES**. Evidence folders exist. But some are incomplete (C4 has no after-fix). |
| Is CURRENT_STATE.md accurate? | **MOSTLY**. Updated with assignment references. But some items marked "PASS current" when they should be "FAIL" (bundle size). |
| Are skills being used or ignored? | **MIXED**. Skills are referenced but execution quality depends on agent. |
| Is validator catching real problems? | **YES**. ALL CHECKS PASSED consistently. Catches format violations, missing sections, stale evidence. |
| Is workflow itself a bottleneck? | **NO**. The workflow is faster than the product. 8 assignments created in one session. |
| What would make the agentic loop 2x more efficient? | **(1)** Auto-run validator after every assignment. **(2)** Auto-update CURRENT_STATE.md. **(3)** Assignment templates with pre-filled evidence paths. |

**Workflow score: 7 / 10**

The workflow system is genuinely good. The problem is not the workflow — it is the product fundamentals (performance, data seeding, deployment).

---

# IMMEDIATE ACTION LIST

## Next 24 Hours
1. **Revert bundle diet changes** — they made the bundle WORSE (318KB → 476KB)
2. **Seed PostgreSQL with data** — killer queries need rows to return answers
3. **Fix killer query pipeline** — `needs_clarification` means the planner is broken for complex queries

## Next 48 Hours
4. **Create AWS account** — unblocks deployment, the #1 funding gate
5. **Generate GPG key** — unblocks audit chain signing
6. **Run C4 profiling** — find the actual bottleneck (embedder? DB pool?)

## Before Any Funding Discussion
7. **Staging URL live** — must be browser-accessible
8. **Killer queries pass live** — all 3 return ≥1 row with correct SQL
9. **C4 P99 < 500ms** — must pass on staging

## Before Professor Walkthrough
10. **Bundle < 250KB** — or at least back to 318KB (revert the failed optimization)
11. **Audit chain signed** — 8/8 founder signatures
12. **Credential rotation approved** — or documented as dummy-only
13. **Run Professor Audit v2 again** — must score ≥ 7/10

---

**AUDITOR CONCLUSION:**

The student has built an **excellent workflow system** and made **real SQL quality improvements** (43/43 Dhairya). But the **product is not ready** for 1 crore. The gap between "tests pass in isolation" and "works under load with real data" is wide.

**Score: 4/10. Not fundable today.**
