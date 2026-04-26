# NRG Frontend Eternal Production Hardening Report

Date: 2026-04-26
Run completed: 2026-04-27 00:12 IST
Auditor: Codex, frontend production hardening pass
Scope: React/Vite frontend, local FastAPI-backed browser verification, production static bundle, Chromium/Firefox/WebKit smoke, desktop/tablet/mobile viewports, Lighthouse, and source-level copy scans.

## Result

Status: production hardened for the audited surfaces.

I am not claiming mathematical absence of every future UI defect across every physical device and institutional environment. The evidence below proves that the critical audited paths are clean in local browser automation: no unexpected console errors, no console warnings, no accepted-path failed network requests, no visible bad runtime literals, no page-level mobile overflow, one query POST under rapid submit, and no visible Tier 3 PII.

## Issues Fixed In This Pass

| Issue | Fix | Files |
|---|---|---|
| Rapid clicking could submit the same query multiple times | Added synchronous in-flight guards and same-query completion cooldowns across all three dashboards | `frontend/src/views/ResearcherDashboard.tsx`, `frontend/src/views/GovernmentDashboard.tsx`, `frontend/src/views/IndustryDashboard.tsx` |
| Mobile page-level horizontal overflow at 375px | Added root overflow containment and constrained scrollable table/tab wrappers | `frontend/src/index.css`, `frontend/src/components/AnswerPanel/AnswerPanel.tsx`, `frontend/src/components/Government/DataTables.tsx`, `frontend/src/components/IntelligenceBrief/components/TabularView.tsx`, dashboard tab bars |
| Font preload warnings polluted browser console | Removed HTML font preloads; kept self-hosted fonts through CSS with `font-display: swap`; updated font-loading test | `frontend/index.html`, `frontend/tests/design-system/font_loading.test.ts` |
| DPDP consent sync failures could write application warnings to console | Replaced console warnings with structured telemetry event `dpdp.sync_failed` | `frontend/src/stores/dpdpStore.ts`, `frontend/src/lib/telemetry.ts` |
| Storybook examples emitted console messages and used non-production titles | Removed console calls and renamed story groups to production framing | Story files under `frontend/src/components/` |
| Static production server lacked full compression/cache behavior and emitted console diagnostics | Added gzip, cache headers, font MIME type, and stdout/stderr helpers | `frontend/e2e-server.js` |
| No stress evidence existed for deep links, offline state, long query, rapid input, or tablet viewport | Added repeatable Playwright stress script and evidence capture | `scripts/audit/frontend_eternal_stress_audit.py` |

## Evidence

Primary stress report: `docs/audits/frontend_eternal_2026-04-26/frontend_eternal_stress_results.json`

Acceptance-path report: `docs/audits/frontend_production_2026-04-26/browser_audit_results.json`

Screenshots:
- `docs/audits/frontend_eternal_2026-04-26/screenshots/01_direct_app_requires_auth.png`
- `docs/audits/frontend_eternal_2026-04-26/screenshots/02_direct_app_after_auth.png`
- `docs/audits/frontend_eternal_2026-04-26/screenshots/03_long_query_hero.png`
- `docs/audits/frontend_eternal_2026-04-26/screenshots/04_offline_banner.png`
- `docs/audits/frontend_eternal_2026-04-26/screenshots/05_desktop_dashboard.png`
- `docs/audits/frontend_eternal_2026-04-26/screenshots/06_rapid_submit_result.png`
- `docs/audits/frontend_eternal_2026-04-26/screenshots/07_source_data_panel.png`
- `docs/audits/frontend_eternal_2026-04-26/screenshots/08_followup_after_stress.png`
- `docs/audits/frontend_eternal_2026-04-26/screenshots/09_tier3_dashboard.png`
- `docs/audits/frontend_eternal_2026-04-26/screenshots/10_tier3_restricted_result.png`
- `docs/audits/frontend_eternal_2026-04-26/screenshots/11_tablet_dashboard.png`
- `docs/audits/frontend_eternal_2026-04-26/screenshots/12_tablet_query_result.png`
- `docs/audits/frontend_eternal_2026-04-26/screenshots/11_mobile_dashboard.png`
- `docs/audits/frontend_eternal_2026-04-26/screenshots/12_mobile_query_result.png`

Recorded acceptance-test artifacts:
- `docs/audits/frontend_eternal_2026-04-26/videos/4ec61969ce5bc8f97a81b1cdab82d46b.webm`
- `docs/audits/frontend_eternal_2026-04-26/videos/a6c2814fc588fd11a619044f597def6f.webm`

Export artifact:
- `docs/audits/frontend_eternal_2026-04-26/downloads/NRG-Intelligence-Brief-1777228739522.html`

Lighthouse:
- `docs/audits/frontend_eternal_2026-04-26/lighthouse/login-page-desktop.report.html`
- `docs/audits/frontend_eternal_2026-04-26/lighthouse/login-page-mobile.report.html`

## Measured Browser Results

| Check | Result |
|---|---:|
| Stress-pass console errors | 0 |
| Stress-pass console warnings | 0 |
| Stress-pass failed requests | 0 |
| Accepted-path unexpected console errors | 0 |
| Accepted-path console warnings | 0 |
| Accepted-path failed requests | 0 |
| Rapid submit POST count | 1 |
| Desktop horizontal overflow | 0 |
| Tablet horizontal overflow | 0 |
| Mobile horizontal overflow | 0 |
| Visible `undefined` / `NaN` / `Infinity` / `Invalid Date` | 0 |
| Tier 3 visible email / Aadhaar / phone matches | 0 |
| Chromium / Firefox / WebKit login smoke | PASS / PASS / PASS |
| Long query retained without overflow | 4,176 chars |
| Answer brief export | PASS |
| Source-data panel | PASS |
| Offline banner | PASS |
| Direct `/app` unauthenticated guard | PASS |

Accepted-path timings from `browser_audit_results.json`:

| Flow | Time |
|---|---:|
| Login page load | 0.75s |
| Researcher login | 1.62s |
| Key query | 0.47s |
| Follow-up query | 1.03s |
| Industry login | 1.67s |
| Tier 3 restricted query | 2.83s |

Lighthouse:

| Mode | Performance | Accessibility | FCP | LCP | TBT | CLS |
|---|---:|---:|---:|---:|---:|---:|
| Desktop | 100 | 95 | 372ms | 420ms | 30ms | 0.000188 |
| Mobile throttled | 85 | 95 | 1,342ms | 2,703ms | 418ms | 0.001634 |

## Commands Run

```bash
npm run build
npm test -- --runInBand
npm run forbidden-grep
NRG_UI_AUDIT_BASE_URL=http://127.0.0.1:3100 NRG_UI_AUDIT_OUT_DIR=docs/audits/frontend_eternal_2026-04-26 .venv/bin/python scripts/audit/frontend_eternal_stress_audit.py
NRG_UI_AUDIT_BASE_URL=http://127.0.0.1:3100 NRG_UI_AUDIT_OUT_DIR=docs/audits/frontend_production_2026-04-26 .venv/bin/python scripts/audit/ui_ux_browser_audit.py
npx --yes lighthouse http://127.0.0.1:3100/ --only-categories=performance,accessibility --preset=desktop
npx --yes lighthouse http://127.0.0.1:3100/ --only-categories=performance,accessibility --form-factor=mobile --screenEmulation.mobile=true
```

## Remaining Risks

Physical iOS and Android devices were not available in this local environment; evidence uses browser mobile and tablet viewports. Institutional SSO was not available; evidence uses the existing local role credentials. The local API used SQLite-backed production seed data; final launch evidence should be repeated against staging PostgreSQL. Mobile throttled Lighthouse LCP is 2.703s, so the strict sub-1.8s mobile LCP target is not fully proven yet even though user-path automation is fast and CLS is effectively zero.

## Sign-Off

I personally ran the audited production paths in browser automation, captured desktop/tablet/mobile screenshots, recorded acceptance-test artifacts, refreshed Lighthouse, and fixed every issue exposed by this pass. I am not certifying impossible absolute perfection; I am certifying that the audited frontend surfaces are materially hardened and currently clean under the evidence listed above.
