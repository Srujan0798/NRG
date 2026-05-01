# Minimax v1.0 Hybrid Fusion - Final Last Pass

Date: 2026-05-01

## Scope

This pass re-used `.claude/skills/hybrid-mvp-fusion/SKILL.md` and the NRG
validation-campaign rules against `/Users/srujansai/Desktop/Minimax_mvp`.

The external v1.0 bundle was treated as source material, not a replacement tree. The
merge target remained the NRG source of truth:

- `Core_Idea_Clean.md`
- `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md`
- `db_struct.sql`
- `prompts_hybrid/00_INDEX.md` through `08_full_coverage_validation_campaign_stone.md`
- `.claude/CURRENT_STATE.md`
- `CORPUS/` after sync verification

## Final Value Extracted

| External v1.0 source | Useful idea | Decision | NRG target | Verification |
| --- | --- | --- | --- | --- |
| `nrg-frontend/src/pages/SearchPage.tsx` sample queries | Reviewer-facing query corpus across researchers, publications, collaboration, funding, TRL, labs, and partnerships | Converted to tests | `tests/api/test_minimax_mvp_fusion_queries.py` | `targeted_minimax_fusion_tests.log` |
| `SearchPage.tsx` TRL sample | "Show TRL stage distribution for technology programs" should produce a clean answer, not a generic formatted workflow dump | Adapted to code | `src/api/main.py` deterministic TRL distribution fast path | `test_minimax_trl_distribution_routes_to_normalized_dhairya_safe_fast_path` |
| `SearchPage.tsx` repeated answer risk | Different visible queries must not collapse into the same answer | Adapted to code/test | Distinct state-wise output route in `_c4_read_model_response` | `test_minimax_sample_queries_have_distinct_verified_nrg_answers` |
| `ResearchersPage.tsx` role-based visibility | Tier 3 must not receive individual identifiers in source rows | Adapted to security policy | `src/auth/rbac_policies.yaml`, `src/api/response_filter.py` | `test_minimax_researcher_sample_is_tier3_safe_through_real_query_contract` |
| External backend security/audit/auth | Simplified implementation with wildcard CORS, mock SQLite, and non-NRG auth/audit contracts | Rejected as direct merge | Existing NRG FastAPI/security/audit stack | Broad backend/security suite |

## Product Changes

1. Added a deterministic fast path for generic TRL stage distribution queries.
   The SQL uses `trl_stages`, orders `Level 1` through `Level 9` numerically,
   and explicitly avoids the Dhairya failure where `TRL 9` is queried as a raw
   stored value. If `trl_stages` returns no rows, the route now reports a
   data-availability gap instead of fabricating fallback stage counts.

2. Added a distinct state-wise research-output response for broad "research
   output by state" queries. This avoids returning the same generic
   publication-by-year answer for unrelated user wording.

3. Hardened Tier 3 response filtering for individual identifiers:
   `researcher_id`, `author_id`, `person_id`, `faculty_id`, `student_id`,
   `employee_id`, `pi_id`, and `investigator_id` are no longer exposed to
   Tier 3. Tier 3 pseudonymous researcher labels are now hash-derived rather
   than raw identifier-derived.

4. Added a regression test file that turns the external v1.0 sample corpus
   into NRG-native API/query checks.

## Verification

| Gate | Result | Evidence |
| --- | --- | --- |
| Targeted final fusion tests | PASS - 40 passed, 1 skipped, 1 deselected | `targeted_minimax_fusion_tests.log` |
| Broad backend/security/query/audit/RAG slice | PASS - 198 passed, 1 skipped, 7 deselected | `backend_security_query_audit.log` |
| Frontend Jest | PASS - 27 suites, 99 tests | `frontend_jest.log` |
| Frontend production build | PASS | `frontend_build.log` |
| CORPUS sync | PASS - `ok: true` | `corpus_sync.json` |
| Raw `/login` + `/query` JSON spot check | PASS - 4 live TestClient requests with audit IDs, citations, TRL rows, and Tier 3 redaction | `raw_json_capture.log` |

## Claim Boundary

`inventory-accounted`: PASS for the Desktop Minimax v1.0 bundle already inventoried in
prior evidence and rechecked in this pass.

`value-integrated`: PASS for the remaining useful query/security value found in
this final pass.

`product-proven`: PASS for the local surfaces covered by the tests above.

Whole-product production superiority is still not claimed. The following gates
remain `BLOCKED` until run in the target environment:

- deployed browser replay using real deployed frontend/API URLs
- production Qdrant/vector baseline
- 1000-user sovereign-cluster C4 load test
- founder GPG signing ceremony

## Files Changed

- `src/api/main.py`
- `src/api/response_filter.py`
- `src/auth/rbac_policies.yaml`
- `tests/api/test_minimax_mvp_fusion_queries.py`
- `evidence/2026-05-01/minimax_fusion_last_pass/*`

## Direct Replacement Decision

The external v1.0 bundle was not deleted and was not used as a replacement tree. It remains
external source material under `/Users/srujansai/Desktop/Minimax_mvp`. Direct
replacement is still rejected because that bundle has mock data, wildcard CORS,
and simplified backend/security/audit/database behavior that conflicts with the
NRG source truth.
