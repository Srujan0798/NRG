# GLM v1.0 Fusion Pass

Date: 2026-05-01

## Scope

This pass used `/Users/srujansai/Desktop/Glm_mvp/workspace-2d7f4a8c-2000-4ff6-853e-a2ff2894fb80` as external source material under the `hybrid-mvp-fusion` workflow.

Direct replacement was rejected. The bundle is a Next.js/Prisma/SQLite application with simplified auth, simplified audit handling, and generated data assumptions. NRG remains FastAPI, React/Vite, local research DB read models, tier-first response filtering, citations, and HMAC audit proof.

## Value Matrix

| GLM source | Useful idea | Decision | NRG target | Gate |
| --- | --- | --- | --- | --- |
| `query-view.tsx` suggested/template queries | Rich reviewer-facing query corpus | Converted to tests | `tests/api/test_glm_fusion_queries.py` | 11 GLM-derived queries must route to distinct verified NRG answers |
| `query-view.tsx` state compare examples | State-vs-state output should not fall into year-only publication output | Adapted into backend route | `src/api/main.py` C4 read model | Gujarat vs Maharashtra returns state-bounded rows |
| `query-view.tsx` renewable publication example | Publication topic questions must not route to funding aggregate | Adapted into backend route | `src/api/main.py` C4 read model | Renewable publication query returns publication rows |
| `query-view.tsx` h-index/citation templates | Aggregate h-index and citation comparisons need first-class routes | Adapted into backend read-model snapshots | `src/api/main.py` | Research-area h-index, citation ranking, institution h-index tests pass |
| `query-view.tsx` IIT/CSIR templates | Institution-family and lab-family questions need bounded answers | Adapted into backend routes | `src/api/main.py` | IIT AI and CSIR lab tests pass |
| `answer-card.tsx` and `source-proof-modal.tsx` | Answer should expose confidence, source rows, SQL, citations, and proof actions | Already present in NRG frontend; used as validation lens | existing frontend tests and build | 99 frontend tests and build pass |
| `worklog.md` QA notes | Empty, error, retry, mobile, and response-shape concerns | Converted to proof expectations | current validation logs | Backend, contract, frontend tests pass |
| Prisma schema and API routes | Stack/schema/auth choices | Rejected as direct merge | none | Preserves `db_struct.sql`, Dhairya audit, tier, and audit chain truth |

## Code Changes

- Added C4 read-model aggregates for:
  - research area average h-index
  - researcher publication counts
  - institution average h-index
  - publication citation totals by area
  - publication citation totals by institution
- Added query routing for:
  - hydrogen catalysis researcher ranking
  - Gujarat vs Maharashtra research-output comparison
  - biotechnology active researchers by state
  - research-area average h-index comparison
  - institution average researcher h-index ranking
  - research-area citation ranking
  - IIT publication citation ranking
  - IIT AI program strength
  - CSIR lab output lookup
  - quantum researcher publication-threshold proxy
  - renewable-energy publication topic lookup
- Tightened the funding-topic fast-path skip so researcher/publication/lab/output questions can route to the bounded C4 read model instead of being forced into funding aggregates.
- Updated `.claude/skills/hybrid-mvp-fusion/SKILL.md` with an external-bundle closure checklist so future agents must account for files, query templates, UI/proof ideas, unsafe stack defaults, highest-risk failing slices, and separated claim statuses.

## Verification

| Check | Result | Evidence |
| --- | --- | --- |
| GLM regression test red phase | 6 failed, 1 passed before patch | terminal output in session |
| GLM regression test after patch | 7 passed | `tests/api/test_glm_fusion_queries.py` run |
| Backend query/security slice | 49 passed, 1 skipped | `backend_query_security_tests.log` |
| Contract and citation slice | 26 passed | `contract_citation_tests.log` |
| Frontend Jest | 27 suites, 99 tests passed | `frontend_jest.log` |
| Frontend production build | passed, built in 51.93s | `frontend_build.log` |
| Corpus sync | ok true | `corpus_sync.log` |
| Ruff on changed Python files | passed | `ruff_check.log` |
| Raw tier JSON samples | 15 responses across Researcher, Government, Industry; all include audit IDs and citations | `raw_json/glm_query_contract_samples.json` |

## Claim Boundary

`inventory-accounted`: GLM source tree and key product files were reviewed for query, UI, API, schema, and evidence value.

`value-integrated`: High-value query and proof ideas were converted into NRG-native backend routes, tests, and evidence.

`product-proven`: The verified scope is local backend/query/security/contract/frontend build coverage listed above. This is not a whole-product superiority claim. Deployed browser replay, production Qdrant baseline, 1000-user cluster C4, and founder signing remain blocked by target deployment and founder-key availability.

## Remaining Blockers

- Production/deployed validation still requires target URLs and cluster context.
- The GLM comparison/chart UI concepts were not copied into frontend code because NRG already has stronger answer/proof surfaces and the backend query issues were higher risk.
- Quantum publication threshold uses visible linked-publication evidence and returns a medium-confidence bounded answer when no local row crosses the requested threshold; it does not invent a >50 result.
