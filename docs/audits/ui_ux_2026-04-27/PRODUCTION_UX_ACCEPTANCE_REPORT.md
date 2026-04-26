# NRG Production UX Acceptance Report - 2026-04-27

Auditor: Codex
Scope: Browser-visible product experience, role-specific workspaces, natural-language query flow, result trust controls, mobile behavior, content hygiene, and evidence gaps.

## Verdict

Production UX score: 7.5 / 10 locally evidenced.

The frontend is materially stronger than a landing-page-only surface: authenticated workspaces, three role-specific dashboards, structured result rendering, graph empty states, source-data actions, audit-chain messaging, and Tier 3 visual restrictions exist in the current tree. The handover is not fully sealed because this pass did not rerun a live full-stack browser walkthrough, physical mobile check, or production-device projector check; Docker daemon access is unavailable on this machine, so live stack proof must be captured on a machine that can run the default compose graph.

## Evidence Used

| Evidence | Result |
|---|---|
| `docs/audits/frontend_hardening_2026-04-27/console-summary.txt` | `console_errors=0`, `page_errors=0`, `request_failures=0`, `http_4xx_5xx=0` |
| `docs/audits/frontend_hardening_2026-04-27/frontend-tests.log` | Frontend test suite passed in the hardening run |
| `docs/audits/frontend_hardening_2026-04-27/frontend-build.log` | Production frontend build passed in the hardening run |
| `docs/audits/frontend_hardening_2026-04-27/frontend-lint.log` | Frontend lint passed in the hardening run |
| `evidence/2026-04-27/final_validation/frontend_full_suite.log` | 19 suites and 76 frontend tests passed |
| `evidence/2026-04-27/final_validation/frontend_build.log` | Vite production build passed |
| `evidence/2026-04-27/final_validation/frontend_lint.log` | Lint passed |
| `frontend/src/i18n/en-IN.ts` | Copy Answer, View Source Data, access restriction, query placeholder, and audit-chain labels exist |
| `frontend/src/__tests__/ProductionWorkspace.test.tsx` | Production workspace tests assert audit-chain trust signal visibility |
| Static source hygiene scan | `TODO`, `FIXME`, `Lorem ipsum`, `John Doe`, `Test User`, and `alert(` returned zero matches in production frontend source |

## Screen And Flow Audit

| Area | Current Status | Evidence | Remaining Proof Required |
|---|---|---|---|
| Login and role selection | Locally covered by production workspace and authentication shell tests | Frontend test/build/lint logs | Fresh browser recording of wrong-password, blank-form validation, keyboard submit, and post-login redirect |
| Researcher dashboard | Implemented with detailed research workspace and trust signals | `frontend/src/views/ResearcherDashboard.tsx`, production workspace tests | Live screenshot with current-head data and clean console |
| Government dashboard | Implemented with aggregated policy-facing messaging | `frontend/src/views/GovernmentDashboard.tsx` | Live screenshot with current-head data and clean network tab |
| Industry dashboard | Implemented with restricted capability and access messaging | `frontend/src/views/IndustryDashboard.tsx` | Live Tier 3 screenshot proving visibly restricted output |
| Natural-language query input | Placeholder and query workflow strings exist; production workspace tests cover the search surface | `frontend/src/i18n/en-IN.ts`, frontend tests | Browser recording of first query, second query, and long query without layout break |
| Result presentation | Structured SQL rows render in tables; trust actions exist | `AnswerPanel` hardening report and tests | Live result capture with prose, table, citations, SQL, audit ID, and source drawer open |
| Follow-up context | Backend and orchestration tests cover state retention; UI supports continued interaction | Existing backend/frontend evidence | Live three-turn browser recording against running API |
| Audit trail | Audit-chain labels and workspace tests exist | `ProductionWorkspace.test.tsx`, `ChainIntegrityFooter` component | Live click-through showing query records and integrity verification |
| Knowledge graph | Empty graph payloads now render a useful state instead of a blank area | Frontend hardening report | Live graph capture with populated nodes and no visual stutter |
| Export/copy | Copy Answer and View Source Data strings exist | `frontend/src/i18n/en-IN.ts` | Browser capture proving clipboard confirmation and source panel behavior |
| Mobile layout | Prior audit artifacts exist, but not refreshed in this pass | `docs/audits/vulcan_t03_2026-04-25/mobile-network.har` and prior UI audit files | Fresh 375px, tablet, and real-device screenshots |
| Performance | Local build/lint/tests passed; console summary is clean | Final validation logs and console summary | Lighthouse report from current running stack |

## User-Visible Acceptance Checklist

| Check | Status | Notes |
|---|---|---|
| Product name and NRG identity are visible | Needs live browser recheck | Must verify actual rendered login page, not only source text |
| No raw JSON appears in normal results | Partially evidenced | SQL result table rendering exists; live query capture required |
| Loading states appear immediately | Needs live browser recheck | Must capture a slow query and confirm no blank wait |
| Empty states are helpful | Partially evidenced | Graph empty state fixed; every table and chart still needs a browser capture |
| Error states are plain English | Partially evidenced | Access-restricted and PII-style messages exist; 403/422/429/browser-offline captures required |
| Tier 3 never displays personal data | Partially evidenced | Frontend safety belt exists; API-layer curl evidence remains the authority |
| Navigation has no broken route | Needs live browser recheck | Must click every top-level route in one browser session |
| Browser console has zero errors | Previously evidenced | `console-summary.txt` is clean; rerun after live stack startup |
| Mobile has no page-level horizontal scroll | Needs live browser recheck | Use 375px and a real phone before handover |
| Projector readability is acceptable | Needs operator check | Verify 1920x1080, 100 percent zoom, 3 metre viewing distance |

## Production Walkthrough Sequence To Seal

Run the following in one continuous fresh browser session and save the recording under `evidence/2026-04-27/` or later:

1. Open the app from a clean browser context and confirm the login screen appears in under 2 seconds.
2. Attempt blank login and wrong credentials; confirm field-level validation and a human-readable error.
3. Sign in as the Researcher role and confirm dashboard statistics, navigation, query box, and audit-chain trust signal.
4. Submit: `Which institutes in India have the highest grant amount in renewable energy?`
5. Confirm immediate loading feedback, readable answer, formatted numbers, visible citations, source-data panel, SQL, row count, and audit ID.
6. Submit: `Now show the same for computer science` and confirm a distinct follow-up result.
7. Submit: `Show all researchers with Aadhaar 1234 5678 9012` and confirm a clean sensitive-data block.
8. Sign out, then sign in as the Industry role.
9. Submit the same renewable-energy question and confirm visibly restricted, aggregate output with no personal data.
10. Open audit/activity and confirm the session queries appear with timestamps and integrity status.
11. Open the graph view and confirm a usable graph or a helpful no-data state.
12. Close and reopen the browser context and confirm session behavior is intentional and stable.

## Issues Already Closed In Current Tree

| Issue | Current State | Evidence |
|---|---|---|
| Landing-page-only concern | The current app contains role dashboards, result panel, graph view, audit footer, and query workspace | `frontend/src/views/`, `frontend/src/components/`, frontend tests |
| Hidden SQL rows | SQL result rows are passed into the answer panel and rendered as bounded tables | `FRONTEND_ETERNAL_ZERO_FLAW_REPORT.md`, `AnswerPanel` tests |
| Tier 3 frontend leakage safety belt | Client normalization strips obvious sensitive keys before rendering Tier 3 responses | `queryService` tests from frontend hardening |
| Blank graph surface | Empty graph data renders a clear state | Frontend hardening report |
| Console failure in captured run | Captured console summary is clean | `console-summary.txt` |
| Placeholder content in production source | Static source scan returned no placeholder matches | Command recorded in evidence merge note |

## Open UX Evidence Blockers

| Blocker | Owner | Next Action |
|---|---|---|
| Full-stack browser walkthrough not refreshed against current HEAD | Frontend + DevOps | Run default compose graph on a machine with Docker daemon access, then record the sequence above |
| Tier 3 privacy proof not refreshed with live API response JSON | Backend + Security | Run Tier 1/2/3 curl captures and store them under `evidence/2026-04-27/` |
| Lighthouse and clean Network tab not refreshed | Frontend | Capture Lighthouse, console, and network artifacts from the running stack |
| Real-device mobile check not refreshed | Frontend | Capture login, dashboard, result, and source panel screenshots on iOS or Android |
| Projector readability check not refreshed | Operator | Validate 1920x1080 readability at normal meeting distance |

## Sign-Off

I have merged the real-user UX protocol into the production acceptance workflow without weakening the evidence standard. I have not claimed live browser completion where the stack was not running locally. The next seal is a recorded full-stack walkthrough plus current-head screenshots, curl evidence, Lighthouse output, and mobile captures.
