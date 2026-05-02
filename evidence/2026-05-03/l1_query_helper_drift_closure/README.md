# L1 Query Helper Drift Closure

Date: 2026-05-03

## Scope

This pass closes the local `L1-CR-006` drift boundary by making the exported
`src/api/query_helpers.py` fast-path helpers delegate to the live answer-engine
implementation in `src/api/main.py`. The old helper copy is no longer the active
answer source for exported helper APIs.

It also preserves and verifies the in-tree null-stat handling and D4 hot-path
index work found at session start.

## Evidence

| File | Result |
| --- | --- |
| `01_targeted_query_security_tests.log` | 10 passed: helper drift regression, P0 security regressions, stats nulls, async query boundary. |
| `02_fast_path_regression_tests.log` | 46 passed: LangGraph API, GLM/Minimax query, final golden fast paths, publication count. |
| `03_py_compile.log` | Python compile check passed for changed backend/test files. |
| `04_migration_contract_tests.log` | 11 passed: D4 hot-path index migration plus D4 data-constraint migration contracts. |
| `05_frontend_build.log` | `npm run build` passed. |
| `06_frontend_lint.log` | `npm run lint` passed. |
| `07_frontend_jest.log` | 32 suites passed, 107 tests passed. |
| `08_frontend_contrast.log` | 1 suite passed, 20 contrast tests passed. |
| `09_git_diff_check.log` | `git diff --check` passed. |
| `10_forbidden_vocab_check.log` | Forbidden-vocabulary guard passed. |
| `11_corpus_sync.log` | Corpus mirror sync passed. |

## Claim Boundary

PASS locally:

- Query helper exported fast paths match live answer-engine shapes for known
  drift cases: TRL distribution, funding agency ranking, funding policy hybrid,
  labs, and researcher statistics.
- `/query` async boundary tests still pass.
- Stats endpoints preserve `NULL` aggregate values instead of fabricating zero.
- Frontend stats cards render missing aggregate values as `Pending`.
- D4 hot-path index migration emits concurrent PostgreSQL index operations and
  skips missing tables/columns.

Still outside this pass:

- Physical removal of the dormant old helper implementation in
  `src/api/query_helpers.py`; this should be done only after a broader route
  extraction pass.
- External deployed, cluster-load, production Qdrant/API, production UAT, and
  founder-signing gates.
