# Frontend Production Hardening Report — 2026-04-27

## Purpose

This document replaces overconfident frontend status language with a developer-verifiable production hardening record. The goal is not to claim perfection. The goal is to make the application more reliable, prove the local checks that actually ran, and clearly identify the remaining evidence needed before handover.

## Areas Reviewed

| Area | Result |
| --- | --- |
| Authentication shell | Single `AuthProvider` now wraps the app tree. |
| Role dashboards | Researcher, Government, and Industry dashboards pass structured SQL rows into result rendering. |
| Query result panel | Backend `sql_results` render as sortable tables instead of being hidden behind prose-only answers. |
| Tier 3 display safety | Client normalization strips obvious PII keys and citation author identity for Tier 3. |
| Graph view | Empty graph payloads render a helpful state instead of a blank surface. |
| Hook hygiene | Persona switching hook dependencies are lint-clean. |

## What Changed

### `frontend/src/App.tsx`

- Removed nested authenticated-route `AuthProvider` instances.
- Kept one top-level provider so route-level pages share the same auth session state.

### `frontend/src/services/queryService.ts`

- Exported `normalizeQueryResponse` so response normalization can be regression-tested directly.
- Added Tier 3 sanitization for obvious sensitive SQL result fields:
  - email
  - phone/mobile
  - Aadhaar
  - PAN
  - direct person/researcher/author identifiers
  - funding/grant/amount fields
- Added citation author removal for Tier 3.

### `frontend/src/components/AnswerPanel/AnswerPanel.tsx`

- Added a `sqlResults` prop.
- Converts backend rows into a bounded, readable table.
- Keeps existing text, statistical, and parsed-table paths intact.

### Dashboard Views

- `ResearcherDashboard`, `GovernmentDashboard`, and `IndustryDashboard` now pass `queryResult.sql_results` into `AnswerPanel`.

### `frontend/src/components/GraphView/GraphView.tsx`

- Added a visible empty state for graph responses with zero nodes.
- Added i18n keys in `frontend/src/i18n/en-IN.ts`.

### `frontend/src/components/PersonaToggle.tsx`

- Memoized persona switching with correct dependencies to keep lint and render behavior clean.

## Tests Added

### Tier 3 sanitization

File: `frontend/tests/lib/queryServiceSanitization.test.ts`

This test proves the frontend removes sensitive fields from Tier 3 normalized responses before rendering. It is a safety belt, not the primary security control.

### SQL result rendering

File: `frontend/tests/components/AnswerPanelSqlResults.test.tsx`

This test proves a prose answer with SQL rows still renders a visible table containing the real query result data.

## Local Verification

Executed from `frontend/` on 2026-04-27:

```bash
npm test -- --runInBand
npm run build
npm run lint
```

Observed results:

- Jest: 18 passed suites, 64 passed tests.
- Build: TypeScript compile and Vite production build passed.
- Lint: passed with no warnings.

## Remaining Non-Local Validation

The following items were not completed in this local pass and should be captured as separate handover evidence:

- Desktop, tablet, and mobile screenshots from the running production stack.
- Real-device iOS and Android smoke tests.
- Lighthouse and browser console reports from the final running environment.
- Full stack `docker compose up` verification on a fresh machine.
- Live API curl checks for Tier 3 PII exclusion.
- Audit chain verification from the running backend.

## Conclusion

The frontend is stronger after this pass: structured results are visible, Tier 3 rendering has an additional privacy guard, graph empty states no longer go blank, and local frontend gates are green. The remaining work is evidence capture from a live full-stack run, not another round of static claims.
