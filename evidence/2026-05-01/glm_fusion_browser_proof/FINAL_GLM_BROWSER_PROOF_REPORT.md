# GLM Fusion Browser Proof

Date: 2026-05-01

## Scope

This pass closes the local browser-proof gap from the GLM second-pass report. It proves the current NRG product can run the GLM-derived visible hydrogen-catalysis suggestion through the actual local FastAPI backend and production frontend build.

It does not claim deployed production readiness, 1000-user cluster performance, or founder signing.

## Files Changed

- `frontend/tests/e2e/glm_visible_query_flow.spec.ts`
  - Added a live Playwright browser proof for the GLM-derived visible suggestion path.
  - The test captures desktop and mobile screenshots, raw Researcher JSON, raw Tier 3 blocked JSON, console errors, and video.

## Flow Proven

1. Researcher login page renders.
2. Researcher logs in with the acceptance credentials.
3. Researcher dashboard renders.
4. Query home renders and shows `Who are the top researchers in hydrogen catalysis?`.
5. User clicks the GLM-derived visible suggestion.
6. Streaming answer starts.
7. Verified answer renders with hydrogen/catalysis content.
8. Citation drawer opens and contains NRG source evidence.
9. Source drawer opens and shows SQL/source-row proof.
10. Audit drawer opens and shows HMAC proof.
11. Mobile viewport still shows the verified answer.
12. Tier 3 PII request is blocked with an audit event ID.

## Evidence

| Evidence | Purpose |
| --- | --- |
| `01_researcher_hydrogen_query_api.json` | Raw Researcher `/query` JSON with audit ID, citations, SQL, source rows, and hydrogen/catalysis answer |
| `02_login_desktop.png` | Login screen |
| `03_researcher_dashboard_desktop.png` | Researcher dashboard after login |
| `04_glm_query_home_desktop.png` | Query home with GLM-derived suggestion visible |
| `05_glm_streaming_planning_desktop.png` | Streaming/planning state |
| `06_glm_answer_verified_desktop.png` | Verified answer |
| `07_glm_citation_drawer_desktop.png` | Citation drawer proof |
| `08_glm_source_data_drawer_desktop.png` | Source data / SQL drawer proof |
| `09_glm_audit_proof_drawer_desktop.png` | Audit/HMAC proof drawer |
| `10_glm_answer_verified_mobile.png` | Mobile answer screenshot |
| `11_tier3_blocked_hydrogen_pii_query.json` | Tier 3 blocked PII query with audit event ID |
| `console_errors.json` | Browser console error capture; result was empty list |
| `glm_derived_visible_query_path_renders_answer_citations_source_rows_audit_proof_and_mobile_view.webm` | Browser recording |
| `backend_uvicorn.log` | Local FastAPI backend startup/request/shutdown log |
| `playwright_glm_visible_query.log` | First browser attempt; failed because the test looked for suggestion chips on the dashboard instead of query home |
| `playwright_glm_visible_query_rerun.log` | Corrected browser proof; passed |

## Commands

```bash
python3 -m uvicorn src.api.main:app --host 127.0.0.1 --port 8021
PLAYWRIGHT_PORT=3021 API_TARGET=127.0.0.1:8021 NRG_EVIDENCE_DIR=../evidence/2026-05-01/glm_fusion_browser_proof npx playwright test -c tests/playwright.config.ts tests/e2e/glm_visible_query_flow.spec.ts
```

Result after correcting the test route assumption:

```text
1 passed (16.0s)
```

## Product-Proof Matrix Update

| Surface | Status After This Pass | Evidence |
| --- | --- | --- |
| Appearance | PASS for the GLM-visible path on local desktop/mobile | Screenshots `02` through `10` |
| UI/UX flow | PASS for local representative flow | Login -> dashboard -> query home -> suggestion -> answer -> citations -> source -> audit -> mobile |
| Query intelligence | PASS for the GLM hydrogen suggestion | Raw API JSON and rendered answer |
| Backend/API | PASS for this path | Raw `/query` JSON with audit ID, citations, SQL/source rows |
| Retrieval | PASS for this path | SQL/source rows in `01_researcher_hydrogen_query_api.json` and source drawer screenshot |
| Security/tier | PASS for Tier 3 block in this path | `11_tier3_blocked_hydrogen_pii_query.json` |
| Audit | PASS for answer and block in this path | Audit IDs in raw JSON plus audit drawer screenshot |
| Accessibility | PARTIAL | Browser flow did not run a dedicated axe/keyboard audit in this pass |
| Performance | PARTIAL | Browser flow elapsed 16.0s; no new load test in this pass |
| Production | BLOCKED | No deployed URL, cluster context, production Qdrant baseline, or founder signing key on this machine |

## Claim Boundary

This pass proves the GLM-derived visible query path locally. It still does not prove absolute whole-product superiority across every surface. The remaining whole-product gates are:

- dedicated accessibility browser audit for the changed path
- fresh load/performance run if speed is claimed
- deployed browser replay
- production Qdrant/RAG baseline
- 1000-user sovereign-cluster C4 run
- founder signing ceremony

## Commit

Pending at report creation time.
