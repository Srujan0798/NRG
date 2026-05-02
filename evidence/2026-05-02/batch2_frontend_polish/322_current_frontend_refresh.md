# Current Frontend Refresh

Date: 2026-05-02

This refresh verifies the current local frontend checkout after the latest
backend/evidence pass. It is local Playwright/build proof, not deployed-browser
proof.

## Status

| Surface | Status | Result |
| --- | --- | --- |
| ESLint | PASS | `npm run lint` exited 0 |
| Jest | PASS | `32 passed, 107 tests passed`; Jest still emits the known open-handle warning after passing |
| Contrast tests | PASS | `1 passed, 20 tests passed` |
| Production build | PASS | `npm run build` exited 0; largest JS asset remains `vendor-recharts-xdmfsjT3.js` at 319.01 kB |
| Focused Playwright a11y/mobile/drawers | PASS | `14 passed` |

## Commands

- `npm run lint`
- `npm test -- --runInBand`
- `npm run test:contrast`
- `npm run build`
- `CI=1 PLAYWRIGHT_PORT=3017 npx playwright test -c tests/playwright.config.ts tests/a11y/axe.test.ts tests/a11y/keyboard.test.ts tests/e2e/mobile_breakpoints.spec.ts tests/e2e/drawer_tiers.spec.ts`

## Boundaries

Deployed frontend URL replay, production network proof, and production mobile
Lighthouse remain external gates.
