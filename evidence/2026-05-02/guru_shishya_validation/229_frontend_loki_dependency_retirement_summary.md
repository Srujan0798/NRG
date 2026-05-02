# Frontend Loki Dependency Retirement

Date: 2026-05-02
Scope: frontend dev-tooling dependency audit reduction

## Change

- Removed unused `loki` visual-regression dependency from `frontend/package.json`.
- Removed the unused `loki:test` script.
- Removed the top-level Loki configuration block.
- Verified no remaining repo references to `loki`, `@loki`, `loki:test`, or `chromeSelector` outside ignored `node_modules`.

## Evidence

| Check | Result | Evidence |
| --- | --- | --- |
| Full npm audit | Exit 1, residual low/moderate only | `221_frontend_npm_audit_after_loki_removal.json` reports 0 critical, 0 high, 18 moderate, 5 low, 23 total |
| High-severity npm audit gate | PASS | `222_frontend_npm_audit_high_after_loki_removal.json` exits 0 with 0 critical/high |
| Frontend lint | PASS | `223_frontend_lint_after_loki_removal.log` exits 0 |
| Production build | PASS | `224_frontend_build_after_loki_removal.log` exits 0 |
| Frontend Jest | PASS | `225_frontend_jest_after_loki_removal.log` reports 27 suites passed, 99 tests passed |
| Contrast regression | PASS | `226_frontend_contrast_after_loki_removal.log` reports 1 suite passed, 20 tests passed |
| Outdated inventory | Captured | `227_frontend_npm_outdated_local_cache_after_loki_removal.json` |
| Loki reference scan | PASS | `228_frontend_loki_reference_check.log` records `rg_exit_code=1`, meaning no matches |

## Residual Risk

Do not claim a clean dependency surface yet. Remaining findings are concentrated
in Storybook/Vite and Jest jsdom chains and require semver-major upgrades or a
formal risk-acceptance decision:

- Storybook chain: `@storybook/*`, `storybook`, transitive `uuid`, transitive
  `esbuild` through Storybook/Vite tooling.
- Vite chain: direct `vite` findings requiring a major upgrade path.
- Jest jsdom chain: `jest-environment-jsdom` through `jsdom`,
  `http-proxy-agent`, and `@tootallnate/once`, requiring Jest 30 migration.
