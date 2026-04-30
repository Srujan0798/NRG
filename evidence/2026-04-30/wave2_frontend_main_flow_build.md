# Wave 2 Frontend Main Flow Build Gate

Date: 2026-04-30

## Scope

Wave 2 was started after Wave 1 stabilized the backend answer contract. This pass focused on restoring the frontend main-flow build gate after the cleanup pass removed `PersonaSheet/PersonaSheet.tsx`.

## Initial Failure

Command:

```bash
cd frontend
npm run build
```

Observed failure:

```text
src/components/PersonaToggle.tsx(5,26): error TS2307: Cannot find module './PersonaSheet/PersonaSheet' or its corresponding type declarations.
```

Cause:

`frontend/src/components/PersonaSheet/PersonaSheet.tsx` was deleted during cleanup, but `PersonaToggle.tsx` still imported it for the mobile persona switcher.

## Fix

Changed `frontend/src/components/PersonaToggle.tsx` so the mobile breakpoint uses a native accessible `<select>` control backed by the same `PERSONAS` array and `switchPersona` handler as the desktop segmented tabs.

This keeps the cleanup direction intact without restoring the deleted sheet component.

The browser suite then exposed a stronger product issue: users could type into the static first-paint boot search before React loaded, but React discarded that pre-hydration query. `frontend/src/App.tsx` now consumes `window.__nrgBootQuery` / `window.__nrgBootSubmit`, stores the query, and routes directly to the answer page or blocked state.

The answer page now also exposes the visible trust contract expected by Wave 2:

- citation drawer has a stable `citation-drawer` test id and HMAC proof when citation audit metadata exists
- audit drawer renders the `HmacProof` component
- source/audit/copy buttons avoid duplicate test ids between nested and route-level controls
- verified answers show a Tier 1 vs Tier 3 comparison panel with an access restriction annotation
- mobile persona switching uses a stable `mobile-persona-switcher` selector

## Verification

Targeted frontend tests:

```bash
cd frontend
npm test -- --runInBand tests/components/PersonaToggle.test.tsx tests/components/AnswerEngineSurface.test.tsx tests/components/StreamingAnswerPanel.test.tsx tests/lib/answerEngineContract.test.ts tests/lib/queryServiceSanitization.test.ts
```

Result:

```text
Test Suites: 5 passed, 5 total
Tests:       12 passed, 12 total
```

After the browser-contract fixes, the expanded targeted component slice was rerun:

```bash
cd frontend
npm test -- --runInBand tests/components/PersonaToggle.test.tsx tests/components/AnswerEngineSurface.test.tsx tests/components/StreamingAnswerPanel.test.tsx tests/components/AnswerTrustActions.test.tsx tests/lib/answerEngineContract.test.ts tests/lib/queryServiceSanitization.test.ts
```

Result:

```text
Test Suites: 6 passed, 6 total
Tests:       13 passed, 13 total
```

Frontend production build:

```bash
cd frontend
npm run build
```

Result:

```text
tsc && vite build --emptyOutDir
2636 modules transformed.
built in 11.52s
```

Focused Playwright main-flow proof:

```bash
cd frontend
npx playwright test -c tests/playwright.config.ts tests/e2e/answer_engine_v1_walk.spec.ts tests/e2e/streaming_answer.spec.ts tests/e2e/citation_drawer.spec.ts tests/e2e/hybrid_proof_acceptance.spec.ts tests/e2e/persona_toggle.spec.ts tests/e2e/audit_panel.spec.ts tests/e2e/mobile_full_flow.spec.ts
```

Result:

```text
9 passed
```

Fresh desktop/mobile screenshot walk:

```bash
cd frontend
npx playwright test -c tests/playwright.config.ts tests/e2e/ui_ux_walk.spec.ts
```

Result:

```text
2 passed
```

## Evidence Paths

This evidence closes the frontend build, component-contract, mocked browser main-flow, audit proof, citation proof, tier comparison, and desktop/mobile screenshot gates.

Fresh screenshot evidence:

- `evidence/2026-04-30/ui_ux/after/login_1366.png`
- `evidence/2026-04-30/ui_ux/after/login_375.png`
- `evidence/2026-04-30/ui_ux/after/hero_1366.png`
- `evidence/2026-04-30/ui_ux/after/hero_375.png`
- `evidence/2026-04-30/ui_ux/after/answer_streaming_1366.png`
- `evidence/2026-04-30/ui_ux/after/answer_streaming_375.png`
- `evidence/2026-04-30/ui_ux/after/answer_final_1366.png`
- `evidence/2026-04-30/ui_ux/after/answer_final_375.png`
- `evidence/2026-04-30/ui_ux/after/audit_list_1366.png`
- `evidence/2026-04-30/ui_ux/after/audit_list_375.png`

## Remaining Wave 2 Work

Live backend browser proof is still pending. The green Playwright path uses mocked SSE and fallback audit data, so it proves frontend behavior and visible states but not live API availability.
