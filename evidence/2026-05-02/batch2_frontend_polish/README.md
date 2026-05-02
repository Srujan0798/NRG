# Batch 2 Frontend Polish Evidence

Date: 2026-05-02
Scope: F2-01 through F2-11 local frontend polish verification.

## Status Matrix

| Task | Status | Evidence |
| --- | --- | --- |
| F2-01 hook dependency lint | PASS | `npx eslint "src/**/*.{ts,tsx}" --rulesdir eslint-rules --rule "react-hooks/exhaustive-deps:error" --format stylish` exited 0 with no output. |
| F2-02 375px and 768px mobile viewports | PASS | `mobile/iphone-se-375.png`, `mobile/ipad-768.png`; Playwright `mobile_breakpoints.spec.ts` passed. |
| F2-03 WCAG axe and keyboard audit | PASS | Playwright axe/keyboard run passed 9 a11y tests; axe JSON files under `frontend/test-results/a11y/`; contrast Jest passed 20/20. |
| F2-04 hardcoded frontend bearer strings | PASS | `rg -n "Bearer" frontend/src frontend/.env*` returned no matches. |
| F2-05 SSE reconnect stability | PASS | Jest `useStreamingQuery` transient reconnect regression keeps stream state/text stable; Playwright measured 121ms recovery with no vertical visual jump in `sse/sse_reconnect_metrics.json`; server stream now advertises 300ms retry. |
| F2-06 fetch abort/timeout | PASS | All `frontend/src` fetches route through `fetchWithTimeout`; Jest timeout/abort tests passed; Playwright navigation instrumentation recorded 0 active `/stats` fetches and 1 aborted request in `network/fetch_abort_navigation.json`. |
| F2-07 actionable error and empty copy | PASS | Existing six empty-state causes covered; generic stream/server copy replaced with actionable copy. |
| F2-08 modal/drawer focus trap | PASS | Jest focus trap tests passed for shared `Drawer` and `Modal`; CitationDrawer and MobileGraphModal use the same hook. |
| F2-09 Tier 1/2/3 drawers | PASS | `drawers/tier{1,2,3}_{citation,source,audit}.png`; Playwright `drawer_tiers.spec.ts` passed. |
| F2-10 bundle budget | PASS | `npm run build` exited 0; largest JS/CSS asset `vendor-recharts-xdmfsjT3.js` is 319,011 bytes; total JS/CSS is 1,279,926 bytes. Vite now errors if any chunk exceeds 500KB or total exceeds 2MB. |
| F2-11 consent banner persistence/revocation | PASS | Jest `ConsentBanner` persistence test and `dpdpStore` revocation test passed. |

## Commands Run

- `npx eslint "src/**/*.{ts,tsx}" --rulesdir eslint-rules --rule "react-hooks/exhaustive-deps:error" --format stylish` -> PASS
- `npm run lint` -> PASS
- `npm test -- --runInBand` -> PASS, 107 tests; WARN: Jest reported an open-handle warning after the passing run.
- `npm run test:contrast` -> PASS, 20 tests
- `npm run build` -> PASS
- `npm audit --audit-level=high` -> PASS, 0 vulnerabilities
- `npx playwright test -c tests/playwright.config.ts tests/a11y/axe.test.ts tests/a11y/keyboard.test.ts tests/e2e/mobile_breakpoints.spec.ts tests/e2e/drawer_tiers.spec.ts tests/e2e/sse_reconnect_stability.spec.ts tests/e2e/fetch_abort_navigation.spec.ts` -> PASS, 16 tests
- `.venv/bin/python -m py_compile src/api/main.py src/api/routes/query.py src/api/query_response_utils.py` -> PASS
- `git diff --check` -> PASS
- `bash scripts/forbidden_vocab_check.sh --all` -> PASS
- `rg -n "Bearer|Something went wrong|dangerouslySetInnerHTML|innerHTML|alert\(" frontend/src frontend/.env* --glob '!frontend/node_modules/**'` -> PASS, no matches
- `rg -n "\bfetch\(" frontend/src --glob '!frontend/node_modules/**'` -> PASS, only `frontend/src/utils/fetchWithTimeout.ts`

## Evidence Files

- `END_TO_END_STEP_CHECK.md`
- `mobile/iphone-se-375.png`
- `mobile/ipad-768.png`
- `drawers/tier1_citation.png`
- `drawers/tier1_source.png`
- `drawers/tier1_audit.png`
- `drawers/tier2_citation.png`
- `drawers/tier2_source.png`
- `drawers/tier2_audit.png`
- `drawers/tier3_citation.png`
- `drawers/tier3_source.png`
- `drawers/tier3_audit.png`
- `sse/sse_reconnect_metrics.json`
- `sse/sse_reconnect_stable.png`
- `network/fetch_abort_navigation.json`
- `frontend/test-results/a11y/login.axe.json`
- `frontend/test-results/a11y/hero.axe.json`
- `frontend/test-results/a11y/founder.axe.json`
- `frontend/test-results/a11y/researcher-dashboard.axe.json`
- `frontend/test-results/a11y/government-dashboard.axe.json`
- `frontend/test-results/a11y/industry-dashboard.axe.json`

## Boundaries

This is local browser/build evidence against the local Playwright server and mocked auth/session streams. Deployed mobile, deployed axe, and production network-tab proof remain external-environment work unless run against deployed URLs.
