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

Frontend production build:

```bash
cd frontend
npm run build
```

Result:

```text
tsc && vite build --emptyOutDir
2636 modules transformed.
built in 7.96s
```

## Remaining Wave 2 Work

This evidence closes the compile and component-contract gate only. Full Wave 2 still needs browser evidence for:

- login -> persona -> dashboard -> query -> streaming answer
- citations/source data drawer
- audit event proof path
- desktop and mobile screenshots
- offline/backend failure/mobile overflow states

Those should be captured after the live stack is running with the stabilized backend query contract.
