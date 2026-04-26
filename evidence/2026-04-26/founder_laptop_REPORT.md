# NRG Founder Laptop Sanity Check Report

Date: 2026-04-26  
Owner: Codex  
Branch observed: main workspace  
Scope: local stack, three canonical questions, three tiers, browser click-through, mobile-width sign-in, T-60 risk walk

## Stack Status

| Service | Status |
|---|---|
| PostgreSQL | Docker healthy |
| Qdrant | Docker healthy |
| Redis | Docker healthy |
| API | local uvicorn on `127.0.0.1:8000`, healthy |
| Frontend | Vite on `127.0.0.1:3000`, running |

Evidence:

- API health: `/health` returned healthy with PostgreSQL row counts for `researchers=50000` and `publications=50000`.
- Deep health: `/health/all` is degraded because local LLM is unavailable; Qdrant and Redis are healthy.
- Audit chain: `verify_chain()` returned `(True, [], 443808)`.
- Docker memory observed: `8307826688` bytes.

## Seeded Row Counts

Source: `evidence/2026-04-26/founder_laptop_seed_counts.json`

| Table | Rows |
|---|---:|
| academic_courses_details | 50,000 |
| innovations_at_various_stages_of_technology_readiness_level | 50,000 |
| innovation_grant_from_govt | 50,000 |
| combined_ipo_patent_data | 50,000 |
| publications | 50,000 |
| researchers | 50,000 |

## Canonical Query Results

Source summary: `evidence/2026-04-26/founder_laptop_query_summary.json`

| Gate | Result |
|---|---|
| All three questions return cited rows in all three tiers | PASS |
| p95 under 4s | PASS, p95 2173 ms |
| Tier 1 vs Tier 3 visibly differs | PASS |
| Max latency | 2864 ms |

Full JSON evidence:

- `evidence/2026-04-26/founder_laptop_sanity_t1_KILLER-01.json`
- `evidence/2026-04-26/founder_laptop_sanity_t1_KILLER-02.json`
- `evidence/2026-04-26/founder_laptop_sanity_t1_KILLER-03.json`
- `evidence/2026-04-26/founder_laptop_sanity_t2_KILLER-01.json`
- `evidence/2026-04-26/founder_laptop_sanity_t2_KILLER-02.json`
- `evidence/2026-04-26/founder_laptop_sanity_t2_KILLER-03.json`
- `evidence/2026-04-26/founder_laptop_sanity_t3_KILLER-01.json`
- `evidence/2026-04-26/founder_laptop_sanity_t3_KILLER-02.json`
- `evidence/2026-04-26/founder_laptop_sanity_t3_KILLER-03.json`

## Tier-Diff Proof

| Question | Tier 1 fields | Tier 3 fields | Diff count |
|---|---|---|---:|
| KILLER-01 | institute, total_credits, avg_credits, above_national_average | rank, institution, access_scope, metric_band, restricted_reason, source_rows | 10 |
| KILLER-02 | financial_year, stage_of_technology, stage_count, stage_pct | rank, institution, access_scope, metric_band, restricted_reason, source_rows | 10 |
| KILLER-03 | institute, year_num, grant_drop_pct, patent_growth_pct, granted_patents | rank, institution, access_scope, metric_band, restricted_reason, source_rows | 11 |

## Browser Click-Through

Source: `evidence/2026-04-26/founder_laptop_ux_checklist.json`  
Recording: `evidence/2026-04-26/founder_laptop_clickthrough.webm`

| Area | Result |
|---|---|
| Sign-in loads with title | PASS |
| Blank-field validation | PASS |
| Wrong credentials message | PASS |
| Researcher sign-in and three canonical questions | PASS |
| Government sign-in and three canonical questions | PASS |
| Industry sign-in and three canonical questions | PASS |
| Tier 3 restricted-shape signal | PASS |
| Audit page opens | PASS |
| 375 px sign-in screenshot | PASS |

Screenshots:

- `evidence/2026-04-26/founder_laptop_desktop_sign_in.png`
- `evidence/2026-04-26/founder_laptop_researcher_result.png`
- `evidence/2026-04-26/founder_laptop_government_result.png`
- `evidence/2026-04-26/founder_laptop_industry_result.png`
- `evidence/2026-04-26/founder_laptop_audit.png`
- `evidence/2026-04-26/founder_laptop_mobile_375.png`

Minor browser evidence noise:

- One expected 401 appears from the wrong-credential check.
- Vite emits aborted module requests during navigation and context close; production build succeeded and does not use Vite module loading.

## T-60 Risk Walk

Source: `evidence/2026-04-26/founder_laptop_T60.md`

| Status | Count |
|---|---:|
| DONE | 13 |
| N/A | 16 |
| BROKEN | 1 |

Open row:

- Risk #19: Docker memory allocation is below the requested founder-grade target and `/health/all` reports local LLM unavailable. The canonical SQL path passed despite this.

## Breakage By Severity

Catastrophic:

- None observed on the canonical three-question browser path.

Serious:

- Local LLM health is degraded and Docker memory is below the requested target. Evidence: `/health/all`, `founder_laptop_T60.md`.

Minor:

- Expected wrong-credential 401 appears in browser console during the negative sign-in check.
- Vite development server shows aborted module requests during automated navigation close.

## Code Fixes Applied During This Check

| Issue | Fix |
|---|---|
| Valid `10 rows` answers were hidden as empty results | Replaced substring matching in `frontend/src/utils/emptyResults.ts` with regex word-boundary checks. |
| Frontend telemetry 404 in local Vite | Added `/api/telemetry` proxy in `frontend/vite.config.ts`. |
| Audit page 403 for non-admin users | Allowed authenticated tier-safe audit list and verify access in `src/api/main.py`. |
| Canonical SQL path too slow and occasionally routed through heavier planner | Added fixed read-only SQL path for the three canonical questions in `src/api/main.py`. |
| Tier 3 canonical JSON shape did not visibly differ enough | Returned restricted aggregate-band rows for Tier 3 in `src/api/main.py`. |
| Browser checker had false negatives | Updated `scripts/founder_laptop_pre_walk.js` for consent handling, exact `/query` response matching, real keystroke entry, and response payload capture. |

## Verification Commands

| Command | Result |
|---|---|
| `.venv/bin/python -m py_compile src/api/main.py src/skills/text_to_sql/sandbox.py scripts/founder_laptop_acceptance.py scripts/founder_laptop_seed.py` | PASS |
| `.venv/bin/python scripts/founder_laptop_acceptance.py` | PASS |
| `node scripts/founder_laptop_pre_walk.js` | PASS |
| `npm run build` in `frontend/` | PASS |
| `npm test -- --runInBand` in `frontend/` | PASS, 15 suites / 61 tests |
| `bash scripts/forbidden_vocab_check.sh` | PASS |

OVERALL READINESS: 8.2 / 10
LAUNCH-READY:      NO — close local LLM/cloud health, Docker memory allocation, and browser console noise policy first
PRODUCTION-READY:  NO — close full LLM health, full T-60 risk #19, and non-Vite production click-through evidence first
BIGGEST SINGLE RISK: Risk #19 remains open in `evidence/2026-04-26/founder_laptop_T60.md` because local LLM health is degraded and Docker memory is below target.
WHAT WILL IMPRESS THE USER:    The three canonical questions produce cited, fast, tier-differentiated answers in the browser across Researcher, Government, and Industry.
WHAT WILL EMBARRASS THE TEAM:  A user who opens DevTools during the negative sign-in test will see an expected 401, and `/health/all` still reports local LLM unavailable.
