# Frontend Dependency Full Audit Closure

Date: 2026-05-02

## Scope

This pass closed the remaining frontend `npm audit` findings after the earlier
high-severity Loki retirement. The production app behavior was not changed.

## Changes

- Upgraded frontend tooling that carried vulnerable transitive chains:
  - Storybook 7 -> Storybook 8.6.18
  - Vite 4 -> Vite 6.4.2
  - Jest/JSDOM 29 -> 30.3.0
  - `@vitejs/plugin-react` 4.0.0 -> 4.7.0
- Removed `@storybook/addon-essentials` because it pulled the vulnerable
  `@storybook/addon-actions -> uuid` path and the repo only needs Storybook for
  component/a11y review.
- Kept `@storybook/addon-a11y` so the story surface remains useful for
  accessibility review.
- Updated the telemetry unit test to use `window.history.pushState()` instead
  of redefining `window.location`, which is not writable in the upgraded JSDOM
  runtime.

## Before / After

| Check | Before | After |
| --- | --- | --- |
| `npm audit` | 18 moderate, 5 low after Loki removal | 0 total vulnerabilities |
| `npm audit --audit-level=high` | PASS | PASS |
| Storybook dependency chain | Storybook 7 plus essentials/actions | Storybook 8.6.18 plus a11y only |
| Frontend build | PASS before this pass | PASS after this pass |
| Jest | PASS before this pass | PASS after this pass |
| Contrast tests | PASS before this pass | PASS after this pass |

## Evidence

- Before audit: `232_frontend_npm_audit_before_storybook_jest_vite_upgrade.json`
- Before dependency tree: `234_frontend_dependency_tree_before_storybook_jest_vite_upgrade.json`
- Intermediate Storybook 8 audit: `235_frontend_npm_audit_after_storybook_8_upgrade.json`
- Final zero-vulnerability audit: `240_frontend_npm_audit_after_storybook_essentials_removal.json`
- Final Storybook tree: `241_frontend_storybook_dependency_tree_after_essentials_removal.log`
- Storybook build: `242_frontend_storybook_build_after_essentials_removal.log`
- Production build: `243_frontend_build_after_dependency_hardening.log`
- Lint: `244_frontend_lint_after_dependency_hardening.log`
- Jest: `245_frontend_jest_after_dependency_hardening.log`
- Contrast: `246_frontend_contrast_after_dependency_hardening.log`

## Result

Frontend dependency audit is now clean locally with `0` total npm audit
vulnerabilities. Storybook, production build, lint, Jest, and contrast checks
all passed after the change.

## Remaining Boundaries

- This is local dependency evidence, not deployed browser evidence.
- Storybook build still emits upstream Storybook/Vite bundle warnings about
  large chunks and Storybook runtime `eval`; these are build warnings, not npm
  audit findings.
- External production gates remain blocked by missing deployed URLs, cluster
  context, production Qdrant target, and founder signing key.
