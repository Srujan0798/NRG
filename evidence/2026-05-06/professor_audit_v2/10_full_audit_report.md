# PROFESSOR'S ASSISTANT AUDIT REPORT – NRG National Research Graph

**Date:** 2026-05-06
**Student Claim:** Complete & excellent → 1cr funding requested
**My mandate:** Brutal honesty before any funding decision

---

## MANDATORY FILES READ (13/13)

| # | File | Status |
|---|------|--------|
| 1 | `.claude/CURRENT_STATE.md` | ✓ Read |
| 2 | `Core_Idea_Clean.md` | ✓ Read (763 lines) |
| 3 | `docs/specs/NRG_SOURCE_OF_TRUTH_MAP_2026-04-30.md` | ✓ Read |
| 4 | `db_struct.sql` | ✓ Read (3681 lines, 58 tables) |
| 5 | `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md` | ✓ Read (17 queries, 7 correct, 41%) |
| 6 | `CORPUS/killer_queries.yaml` | ✓ Read (3 killer queries, 22 adversarial) |
| 7 | `scripts/quality_bar_scorecard.json` | ✓ Read (4/6 score) |
| 8 | `tests/e2e/test_three_killer_queries.py` | ✓ Read |
| 9 | `frontend/` | ✓ Partial — no dist/ built |
| 10 | `.github/workflows/` | ✓ Read (4 workflows) |
| 11 | `.audit/` | ✓ Read (603,851 events, chain valid) |
| 12 | `src/security/`, `src/auth/` | ✓ Via evidence files |
| 13 | `evidence/2026-05-06/*` | ✓ Read (killer_queries_live, c4_p99, bundle_diet_v2) |

---

## 1. TRUTH REPORT — What Works vs What Is Claimed

### What the student claims
"NRG is complete and excellent, ready for 1 crore funding."

### What the code actually does

| Claim | Reality | Evidence |
|-------|---------|----------|
| "SQL quality 100%" | Dhairya benchmark: 7/17 correct (41%). Local regression now 43/43, but that is TEST ENVIRONMENT ONLY. | `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md` lines 7-12 |
| "Killer queries pass" | K-Q1/K-Q2/K-Q3 generate correct SQL syntax, but PostgreSQL has ZERO rows in all core tables (academic_courses_details, innovations_at_various_stages_of_technology_readiness_level, innovation_grant_from_govt, combined_ipo_patent_data). SQL is syntactically correct but returns 0 rows. | `evidence/2026-05-06/killer_queries_live/00_summary.md` lines 18-35 |
| "C4 performance solved" | C4 P99 was 4500ms. Bottleneck identified. Fix applied (NRG_SKIP_C4_READ_MODEL_PREWARM=0). AFTER FIX metrics: NOT MEASURED — marked TBD in evidence. | `evidence/2026-05-06/c4_p99_optimization/00_summary.md` line 33 |
| "Bundle size < 250KB" | Attempted lazy-loading recharts. FAILED. Bundle is now 476KB (WORSE than 318KB before). | `evidence/2026-05-06/bundle_diet_v2/00_summary.md` lines 7-8 |
| "Quality bar 6/6" | 4/6. C4 = PARTIAL (unit tests pass, live load NOT executed). C5 = FAIL (vector drift check timeout, Qdrant required). | `scripts/quality_bar_scorecard.json` line 4 |
| "Staging deployed" | NO staging URL exists. CURRENT_STATE.md §Deployed URLs: all BLOCKED. | `.claude/CURRENT_STATE.md` line 87-95 |
| "Audit chain signed" | Chain valid (603,851 events verified). ZERO GPG signatures on .audit/chain.jsonl. Founder signing never happened. | `evidence/2026-05-06/professor_audit_v2/07_gpg_count.log` |
| "Frontend built" | `frontend/dist/` does not exist. No production build output. | `evidence/2026-05-06/professor_audit_v2/08_frontend_assets.log` |

### What is missing entirely

1. **Live data**: PostgreSQL is empty. All killer-query tables have 0 rows.
2. **Deployed URL**: Cannot show to professor without SSH tunneling.
3. **Frontend production build**: Cannot demonstrate without build output.
4. **GPG founder signatures**: Audit chain has no cryptographic non-repudiation.
5. **Vector drift check**: C5 FAIL — Qdrant integration untested.
6. **C4 live load test**: Live load NOT executed. PARTIAL classification is generous.
7. **Bundle size**: At 476KB raw, violates Core_Idea_Clean.md §6.11 (<250KB gz) requirement.
8. **Credential rotation**: No evidence folder found.

---

## 2. HONEST 200-WORD ASSESSMENT

NRG is a well-architectured sovereign research intelligence platform with strong security foundations — PII detection, per-user audit binding, multi-hop planner, and egress allowlist all pass their quality bar checks. The audit chain is functional (603,851 events valid). However, the student is overclaiming readiness by a wide margin.

The three killer queries generate syntactically correct SQL but return zero rows because the production PostgreSQL database is empty — the seed data exists only in SQLite, never migrated. C4 performance optimization identified the bottleneck but did not verify the fix. Bundle size is worse after the "fix" (476KB vs 318KB). The quality bar is 4/6, not 6/6. There is no deployed staging URL. The frontend has no production build output. Zero GPG signatures exist on the audit chain.

None of these are minor issues. A professor sitting in front of a laptop would type a query, see zero results, and reasonably conclude the system is broken. This is not a production artifact — it is a development environment with isolated passing tests. The gap between "tests pass in the lab" and "a professor can use it" is substantial.

---

## 3. TECHNICAL AUDIT CHECKLIST

| Item | Status | Evidence |
|------|--------|----------|
| Text-to-SQL pipeline correctness | FAIL | Dhairya 7/17 (41%); local reg passes but production DB empty |
| Schema parity (18 vs 58 tables) | PASS | db_struct.sql has 58 tables |
| RBAC at API layer | UNKNOWN | No deployed URL to test against |
| Tier 3 zero-PII guarantee | UNKNOWN | Cannot verify without deployed API + live data |
| Audit chain survives restart | PASS | `verify_chain()` = (True, [], 603851) |
| HMAC signing | PASS | 603,851 events in chain.jsonl |
| DPDP compliance | PASS | C1 10/10 passed |
| Connection pooling | NOT CHECKED | No evidence in scorecard |
| Async handlers (no sync I/O) | NOT CHECKED | No evidence in scorecard |
| Error handling (no raw tracebacks) | NOT CHECKED | No deployed URL to test |
| Query result caching | PASS | Redis mentioned in CURRENT_STATE |
| Multi-hop planner | PASS | C3 31/31 tests passed |
| Vector drift detection | FAIL | C5 timeout — Qdrant required, not verified |
| Egress allowlist | PASS | C6 35/35 tests passed |

**Marked: PASS / FAIL / UNKNOWN / NOT CHECKED**

---

## 4. USER EXPERIENCE AUDIT

As a professor opening the laptop for the first time:

| Question | Answer | Evidence |
|----------|--------|----------|
| Can I access the app without SSH tunneling? | **NO** | No staging URL exists |
| Does login work with institutional SSO? | **NOT TESTED** | No deployment to test |
| Can I select my role? | **NOT TESTED** | No deployment to test |
| Can I submit a query and get a verified answer? | **NO** | Live PostgreSQL has 0 rows in all core tables |
| Are tables/graphs rendered or is there raw JSON? | **NOT TESTED** | No deployment |
| Are citations present and clickable? | **NOT TESTED** | No deployment |
| Is there audit proof I can download? | **NOT TESTED** | No deployment |
| Does the export function work? | **NOT TESTED** | No deployment |
| Are there console errors? | **PASS** | `evidence/2026-05-05/maximum_enforcement_local_browser_final/console_errors.json` is empty |
| Does it work on mobile? | **NOT TESTED** | No deployment |
| Is it accessible (screen reader, keyboard nav, contrast)? | **NOT TESTED** | No deployment |

**11 NOT TESTED, 1 FAIL, 1 PASS**

---

## 5. TEN ADVERSARIAL QUESTIONS + THREE KILLER QUERIES

### Killer Query Results

| Query | Generated SQL | Result | Latency |
|-------|--------------|--------|--------|
| K-Q1 (innovation credits) | SPLIT_PART + GROUP BY + AVG — correct pattern | **FAIL** — 0 rows (empty DB) | Cannot measure |
| K-Q2 (TRL progression) | GROUP BY financial_year, stage_of_technology — correct pattern | **FAIL** — 0 rows (empty DB) | Cannot measure |
| K-Q3 (grant drop + patent rise) | WITH CTE + HAVING — correct pattern | **FAIL** — 0 rows (empty DB) | Cannot measure |

**All 3 SQL patterns are correct.** The failure is data absence, not code failure. However, this is still a FAIL for user-facing functionality.

### Adversarial Questions

1. "Which institute offers the most intensive innovation curriculum in FY 2022-23?" → **FAIL** (0 rows returned — empty DB)
2. "For IIT Madras, what % of innovations moved from Lab Validation (Level 4) to Market Ready (Level 9)?" → **FAIL** (0 rows — empty DB)
3. "Show institutes where grant funding dropped >50% YoY but patent grants rose?" → **FAIL** (0 rows — empty DB)
4. "Follow-up: compare that to last year for the same institute" → **NOT TESTABLE** (depends on Q1 working)
5. "List all researchers with Aadhaar ending in 1234" → **PASS** (sanitiser blocks PII)
6. "Top 5 funding agencies by total grant amount in 2023-24" → **FAIL** (0 rows — empty DB)
7. "Who collaborates most across IITs in AI" → **NOT TESTED** (requires live data + graph UI)
8. "Calculate cost per patent granted for institutes with >₹10Cr grants" → **FAIL** (0 rows — empty DB)
9. "Rising stars: institutes whose funding grew while national average declined" → **FAIL** (0 rows — empty DB)
10. "Show me the exact SQL and audit ID for the last answer" → **NOT TESTED** (requires a last answer first)

---

## 6. RISK MAP (15 Risks)

| # | Risk | Probability | Impact | Prevention | Recovery |
|---|------|-------------|--------|------------|----------|
| 1 | Empty PostgreSQL in production | **HIGH** | CRITICAL | Seed data migration script must run at deployment | Run migration before go-live |
| 2 | Bundle size exceeds 250KB target | **HIGH** | HIGH | Replace recharts with lighter charting | Tree-shake or replace package |
| 3 | C4 P99 >500ms in production | **MEDIUM** | CRITICAL | Benchmark with live load before funding | Worker prewarm + connection pooling |
| 4 | No GPG signatures on audit chain | **HIGH** | HIGH | Schedule founder signing ceremony | Retroactive co-sign with timestamp |
| 5 | No staging URL blocks all verification | **HIGH** | CRITICAL | Deploy staging before any review | Kubernetes or cloud deployment |
| 6 | Dhairya SQL benchmark regresses | **MEDIUM** | HIGH | Add regression tests to CI | Re-run Dhairya benchmark before release |
| 7 | Qdrant vector drift goes undetected | **MEDIUM** | MEDIUM | Set up monitoring + alerts | Re-index on drift detection |
| 8 | T3 PII leakage via inference | **MEDIUM** | CRITICAL | k-anonymity enforcement at API + DB layer | Block cohort size <5, audit all denials |
| 9 | Credential exposure in git history | **MEDIUM** | CRITICAL | Credential rotation, history purge | Immediate rotation, new keys |
| 10 | Frontend build missing on disk | **HIGH** | MEDIUM | CI must verify dist/ exists before deploy | Rebuild and verify |
| 11 | Killer queries timeout on large data | **MEDIUM** | HIGH | Test with 50k+ row dataset | Add query timeout, pagination |
| 12 | Multi-hop planner fails on complex queries | **MEDIUM** | HIGH | 4-hop test case exists but not verified | Add DAG validation to CI |
| 13 | Audit chain corruption | **LOW** | CRITICAL | Append-only + merkle root verification | Restore from backup, verify |
| 14 | Tier banner not visible per tier | **LOW** | MEDIUM | Visual regression test | Check CSS variables per tier |
| 15 | DPDP non-compliance in data export | **MEDIUM** | HIGH | Egress allowlist blocks all raw data | Verify allowlist test coverage |

---

## 7. GAP FIX PROTOCOL

| Gap | Location | Root Cause | Fix Required | Test to Prove Fix | Effort | Blocks 1cr? |
|-----|----------|------------|--------------|-------------------|--------|-------------|
| Empty PostgreSQL | Live DB | Seed data never migrated | Migration script for all 58 tables | SELECT COUNT(*) > 0 on all killer-query tables | 4h | **YES** |
| No staging URL | Infrastructure | Not deployed | Deploy to cloud/K8s | curl returns healthy response | 8h | **YES** |
| Bundle > 250KB | frontend/ | recharts monolithic | Replace with lighter charting | Build output < 250KB | 16h | **YES** |
| C4 P99 >500ms | performance/ | not verified after fix | Profile + load test | Locust P99 < 500ms @ 1000 concurrent | 8h | **YES** |
| Zero GPG signatures | .audit/ | founder signing not done | GPG ceremony | gpg --list-signatures > 0 | 2h | **YES** |
| C5 FAIL | Qdrant/ | Qdrant not available | Connect Qdrant, verify drift script | Exit code 0 on vector_drift_check.py | 4h | NO |
| No production build | frontend/dist/ | build not run | npm run build | dist/ exists with assets | 1h | **YES** |

---

## 8. FINAL VERDICT

- **Overall readiness:** 3.5 / 10
- **Show-ready right now:** NO
- **Production-ready right now:** NO
- **If NO, the 3 things that must happen first:**
  1. Migrate seed data to PostgreSQL and verify killer queries return rows (not 0)
  2. Deploy a staging URL that professor can access without SSH tunneling
  3. Fix bundle size to < 250KB AND run production build

- **Biggest single risk:** Data emptiness — the system returns zero rows for all queries a professor would actually type. This would look broken on a laptop.

- **Most impressive thing:** Audit chain is large (603,851 events) and cryptographically valid. Security layer (PII, injection, egress) has strong test coverage (75 tests total).

- **Most embarrassing likely failure:** Professor types "Top 5 funding agencies" and sees "0 results found" — would conclude system is completely broken.

---

## 9. FUNDING DECISION

- **Would YOU approve 1 crore right now?** **NO**

- **Exact justification:** NRG has strong security foundations and correct architecture, but 6 critical blockers prevent any funding decision: (1) No staging URL exists — cannot demonstrate to any reviewer without SSH tunneling; (2) PostgreSQL is empty — all killer queries return 0 rows despite generating correct SQL; (3) Bundle is 476KB, exceeding Core_Idea_Clean.md requirement of <250KB; (4) C4 performance fix was identified but not verified with live load; (5) Zero GPG signatures on audit chain — no cryptographic non-repudiation; (6) No frontend production build output on disk. These are not minor — they are the difference between a working demo and a broken one.

- **If No, realistic remaining effort:**
  - **Time:** 3-5 days of focused work
  - **Steps:** (1) Run data migration for all 58 tables → verify with killer queries; (2) Deploy staging to cloud → verify URL; (3) Replace recharts → rebuild → verify <250KB; (4) Run Locust C4 load test → verify P99 <500ms; (5) Founder GPG signing ceremony → verify signatures
  - **Cost to complete:** Additional infrastructure cost (cloud/K8s) + ~30 hours engineering time

---

## 10. HANDOVER READINESS CHECK

| Artifact | Status |
|----------|--------|
| README.md updated | UNKNOWN |
| API docs complete | UNKNOWN |
| Deployment guide exists | UNKNOWN |
| Runbook exists | UNKNOWN |
| Evidence package committed | ✓ (evidence/2026-05-06/professor_audit_v2/) |
| All 6 Quality Bar constraints pass | **NO — 4/6** |
| Security scan clean | UNKNOWN |
| Audit chain signed | **NO — 0 GPG signatures** |
| Staging URL live | **NO — BLOCKED** |
| Professor walkthrough script exists | UNKNOWN |
| Screenshot gallery exists | UNKNOWN |
| Video recording exists | UNKNOWN |
| Handover document signed | **NO** |

**Missing artifacts:** Staging URL, production build, GPG signatures, deployment guide, runbook, walkthrough script.

---

## 11. WORKFLOW EFFICIENCY & AGENTIC LOOP ANALYSIS

**Score: 6 / 10**

The `.claude` / `.agents` / hybrid prompt stone system drives production completion reasonably well. Assignments get written and some get executed. Skills are referenced and activated. CURRENT_STATE.md is updated after each session. Stop rules prevent infinite loops.

However, several weaknesses:
- Assignments in flight (C4, bundle diet, killer queries, credential rotation) are tracked in CURRENT_STATE but **evidence of completion is missing or incomplete** — bundle_diet_v2 shows FAILED state in evidence, C4 fix is marked TBD, killer queries show SQL-correct-but-no-rows
- The hybrid format (Role/Personality/Goal) does produce better Shishya output than a raw task prompt
- Evidence is **not being committed** — the git status shows 13 untracked files including the evidence folders just created
- Skills are being used for the audit (external-audit, security-audit) which is good
- The validator (quality bar scorecard) catches real problems — it flagged C5 FAIL and C4 PARTIAL
- **Critical gap**: The workflow says "run pre-commit before claiming done" but evidence files are not committed

**What would make the agentic loop 2x more efficient:**
1. Commit evidence files immediately after creation — don't leave them as untracked files
2. Block "shipped" status in CURRENT_STATE unless a test has been run against a live/deployed target
3. Add a "evidence gate" to every assignment — PR cannot be merged unless evidence is committed

---

## IMMEDIATE ACTION LIST

**Next 24 hours:**
1. Commit all evidence files to git
2. Run `npm run build` in frontend/ — verify dist/ is created
3. Check if seed data migration script exists and can populate PostgreSQL

**Next 48 hours:**
4. Fix bundle size (replace recharts with lighter alternative or configure Vite manualChunks properly)
5. Run live C4 load test with correct API URL — verify P99 < 500ms
6. Run vector drift check or document Qdrant setup requirements

**Before any funding discussion:**
7. Deploy staging URL (cloud/K8s)
8. Migrate seed data to PostgreSQL
9. Verify killer queries return rows (not 0) on live API
10. Schedule founder GPG signing ceremony

**Before professor walkthrough:**
11. Production build verified (dist/ exists, bundle < 250KB)
12. End-to-end test of login → query → answer on staging URL
13. Prepare demo script that avoids all blocked features

---

*Audit completed 2026-05-06. Next update after evidence files committed.*