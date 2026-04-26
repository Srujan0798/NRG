# Production Web App Status — 2026-04-27

## Scope

This report covers the local frontend production hardening completed on 2026-04-27. It records code changes and reproducible local checks only. It does not claim external infrastructure acceptance, physical-device testing, production data acceptance, or funding readiness beyond what was verified in this workspace.

## Current Application Shape

The NRG web application is not just a front page. The checked-in frontend contains:

- Authentication and role selection.
- Researcher, Government, and Industry dashboard views.
- Natural-language query flow with audit-aware result panels.
- SQL visibility, citation drawer, graph view, export actions, and trust actions.
- Audit trail and audit event pages.
- System and metrics views used for operational visibility.

## Issues Fixed In This Pass

1. **Auth provider duplication removed**
   - File: `frontend/src/App.tsx`
   - The authenticated route tree now uses one top-level `AuthProvider`, avoiding split auth state across nested providers.

2. **Structured SQL rows now render in production result panels**
   - File: `frontend/src/components/AnswerPanel/AnswerPanel.tsx`
   - `AnswerPanel` now accepts `sqlResults` directly and renders a real table from backend `sql_results`, even when the natural-language answer is prose.

3. **Role dashboards now pass SQL rows to the result component**
   - Files:
     - `frontend/src/views/ResearcherDashboard.tsx`
     - `frontend/src/views/GovernmentDashboard.tsx`
     - `frontend/src/views/IndustryDashboard.tsx`
   - The visible result table now reflects the backend query payload rather than relying only on text parsing.

4. **Tier 3 frontend PII safety belt added**
   - File: `frontend/src/services/queryService.ts`
   - `normalizeQueryResponse` now strips sensitive SQL result keys and citation author identity before rendering Tier 3 data. This is a frontend defense-in-depth layer and does not replace backend enforcement.

5. **Graph empty state hardened**
   - Files:
     - `frontend/src/components/GraphView/GraphView.tsx`
     - `frontend/src/i18n/en-IN.ts`
   - Empty graph responses now show a clear, localized empty state instead of a blank panel.

6. **Persona toggle lint issue fixed**
   - File: `frontend/src/components/PersonaToggle.tsx`
   - `switchPersona` is now memoized with correct hook dependencies.

## Reproducible Evidence

Run from the repository root:

```bash
cd frontend
npm test -- --runInBand
npm run build
npm run lint
```

Verified locally on 2026-04-27:

- `npm test -- --runInBand`: 18 suites passed, 64 tests passed.
- `npm run build`: TypeScript and Vite production build passed.
- `npm run lint`: passed with no warnings.

## New Regression Coverage

- `frontend/tests/lib/queryServiceSanitization.test.ts`
  - Proves Tier 3 response normalization strips obvious PII fields and citation authors before UI rendering.

- `frontend/tests/components/AnswerPanelSqlResults.test.tsx`
  - Proves `AnswerPanel` renders real `sql_results` rows as a table even when answer text is prose.

## Remaining Evidence Required Before External Handover

These are not code blockers from this pass, but they must be captured before a formal external handover:

- Fresh desktop, tablet, and mobile screenshots from the running stack.
- Real iOS and Android smoke checks.
- Browser console capture proving no runtime errors in the target environment.
- `docker compose up` verification on the handover machine.
- Live backend curl proof that Tier 3 never receives PII from the API, independent of the frontend safety belt.

## Status

Local frontend code gates pass and the query result path is materially stronger than before this pass. The handover evidence should now be completed with a running full-stack capture rather than relying on static claims.
