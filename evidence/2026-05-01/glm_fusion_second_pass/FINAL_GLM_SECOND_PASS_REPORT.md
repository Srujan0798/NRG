# GLM External Bundle Fusion - Second Pass

Date: 2026-05-01

## Status

| Status Type | Result |
| --- | --- |
| inventory-accounted | PASS for the GLM external bundle inventory captured in this pass |
| value-integrated | PASS for visible query suggestions and tests converted into NRG-native surfaces |
| product-proven | PARTIAL: local frontend/backend/security slices passed; deployed production, cluster load, and founder-signing gates remain BLOCKED |

This pass does not claim the whole product is "100% better" in every corner. It proves the specific GLM-derived visible query value that was integrated, and records the remaining gates honestly.

## Source Material Inspected

- External bundle path: `/Users/srujansai/Desktop/Glm_mvp/workspace-2d7f4a8c-2000-4ff6-853e-a2ff2894fb80`
- Inventory evidence: `evidence/2026-05-01/glm_fusion_second_pass/glm_bundle_file_inventory.txt`
- Value-signal scan: `evidence/2026-05-01/glm_fusion_second_pass/glm_value_signals.txt`

Inventory count from this pass: 598 files, including external `src/`, `skills/`, `download/`, `upload/`, scripts, configs, screenshots, local database artifacts, and work logs.

## Decisions

| Source Area | Decision | NRG Outcome |
| --- | --- | --- |
| GLM query examples and suggestion labels | Adapt | Promoted verified GLM query shapes into NRG visible suggestion chips and hero copy |
| GLM Next.js/Prisma/API defaults | Reject direct merge | NRG keeps FastAPI, current auth, `db_struct.sql`, tier policy, citations, source rows, and audit IDs |
| GLM UI proof/citation concepts | Adapt | Kept NRG answer-engine flow primary: query -> streaming answer -> citations/source -> audit proof |
| GLM generic skill library | Park | Treated as external source material only; not copied into runtime product |
| GLM screenshots/evidence exports | Use as design signal only | Not treated as NRG product proof |
| GLM local databases and generated artifacts | Reject direct merge | NRG source truth remains current schema/corpus and live read models |

## Code Changes

- `frontend/src/views/AnswerEngine.tsx`
  - Replaced old persona suggestion chips with backend-verified GLM-derived queries.
  - Removed one unrouted industry suggestion after backend contract evidence showed it did not route.
- `frontend/src/i18n/hero-copy.ts`
  - Updated hero placeholders and default suggestions to verified query shapes.
- `frontend/src/i18n/en-IN.ts`
  - Mirrored the visible query updates for localized copy.
- `frontend/tests/components/AnswerEngineSurface.test.tsx`
  - Asserted researcher and industry suggestions use the verified GLM-derived query set.
- `frontend/tests/components/SuggestionChips.test.tsx`
  - Asserted the default suggestion chip submits the verified hydrogen-catalysis query.
- `frontend/tests/components/QueryWorkbench.test.tsx`
  - Updated the mocked proof payload and expected submitted chip to match the verified query path.

## Query Contract Proof

Evidence files:

- `visible_query_chip_backend_contract.json`
- `visible_query_chip_live_api_contract.json`

Results:

- 12 visible suggestion queries routed through the backend fast path.
- 12 live `/query` requests passed across Researcher, Government, and Industry.
- Every live response included the expected tier, citations, source rows, and `audit_event_id`.
- Tier 3 intentionally hides SQL text while preserving citations, source rows, and audit proof.

## Validation Commands

| Command | Result | Evidence |
| --- | --- | --- |
| `npm --prefix frontend test -- tests/components/AnswerEngineSurface.test.tsx tests/components/SuggestionChips.test.tsx --runInBand` | PASS, 9 tests | `frontend_focused_tests.log` |
| `python3 -m pytest tests/api/test_glm_fusion_queries.py tests/api/test_minimax_mvp_fusion_queries.py -q` | PASS, 10 tests | `backend_glm_minimax_tests.log` |
| `python3 scripts/verify_corpus_sync.py` | PASS | `corpus_sync.log` |
| `python3 -m ruff check src/api/main.py tests/api/test_glm_fusion_queries.py tests/api/test_minimax_mvp_fusion_queries.py` | PASS | `ruff_check.log` |
| `python3 -m pytest tests/security/test_security_hardening.py tests/security/test_hmac_validation.py -q` | PASS, 22 tests | `security_hmac_slice.log` |
| `npm --prefix frontend test -- --runInBand` | First run found one stale test expectation; rerun passed 99 tests | `frontend_jest_full.log`, `frontend_jest_full_rerun.log` |
| `npm --prefix frontend run build` | PASS | `frontend_build.log` |
| `git diff --check` | PASS | terminal output before commit |

## Product-Proof Matrix

| Surface | Current Status | Evidence / Blocker |
| --- | --- | --- |
| Appearance | PARTIAL PASS | Unit/component and build proof only in this pass; no new browser screenshots created in this pass |
| UI/UX flow | PARTIAL PASS | Suggestion-chip and answer-engine surface tests passed; prior browser proof remains in earlier evidence |
| Query intelligence | PASS for GLM-visible query chips | Backend fast-path and live API contract JSON show all 12 visible chips route |
| Database/schema | PASS for corpus sync | `corpus_sync.log` |
| Dhairya audit alignment | PASS for covered external query regressions | GLM/Minimax backend tests passed |
| Backend/API contract | PASS for covered chips | `visible_query_chip_live_api_contract.json` |
| Retrieval | PASS for covered SQL/read-model paths | Source rows and citations present in API contract JSON |
| Security/tier | PASS for local slice | `security_hmac_slice.log`; Tier 3 live chip responses preserved audit/citations/source rows |
| Audit | PASS for covered chips | All 12 live responses included `audit_event_id` |
| Accessibility | PARTIAL PASS | Existing Jest a11y/contrast suite passed in full frontend rerun |
| Performance | UNKNOWN for this pass | No new load test was run in this second pass |
| Evidence | PASS | This report plus command logs and raw JSON evidence |
| Deployed production | BLOCKED | No production URL, cluster context, or founder signing key available on this machine |

## Blockers / Non-Claims

- This pass does not prove deployed production readiness.
- This pass does not prove 1000-user cluster C4.
- This pass does not create new desktop/mobile screenshots.
- This pass does not replace NRG architecture with the external bundle.
- The old GLM external bundle is not a runtime dependency; useful value was converted into NRG-native frontend copy/tests and previously committed backend query routes.

## Commit

Pending at report creation time.
