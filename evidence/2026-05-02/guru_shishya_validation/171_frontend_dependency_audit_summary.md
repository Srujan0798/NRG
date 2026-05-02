# Frontend Dependency Audit Summary

Date: 2026-05-02

## Evidence

- `169_frontend_npm_audit_current.json`
- `170_frontend_npm_outdated_current.json`
- `179_frontend_npm_audit_high_after_tooling_update.json`
- `180_frontend_npm_outdated_after_tooling_update.json`
- `185_frontend_build_after_lint_cleanup.log`
- `186_frontend_jest_after_lint_cleanup.log`
- `187_frontend_lint_after_lint_cleanup.log`
- `188_frontend_contrast_after_lint_cleanup.log`
- `189_frontend_npm_audit_high_final_after_lint_cleanup.json`
- `190_frontend_dependency_tree_after_lint_cleanup.log`

## Before

The starting `npm audit` JSON reported 39 vulnerabilities:

- critical: 0
- high: 10
- moderate: 23
- low: 6

Dependency count from the audit metadata:

- production: 201
- development: 1167
- optional: 27
- total: 1368

## Change

Updated the vulnerable frontend dev-tooling chain:

- Storybook packages from `7.6.20` to `7.6.24`
- `@typescript-eslint/eslint-plugin` and `@typescript-eslint/parser` from v6 to v8
- `eslint` to `8.57.1`
- added a `tar` override at `7.5.13` so Storybook CLI no longer resolves the vulnerable tar chain

## After

`npm audit --audit-level=high --json` now exits 0. The final audit JSON reports 31 remaining low/moderate vulnerabilities:

- critical: 0
- high: 0
- moderate: 25
- low: 6

Dependency count from the final audit metadata:

- production: 202
- development: 1167
- optional: 27
- total: 1369

## Verification

- `npm run build`: passed
- `npm test -- --runInBand`: passed, 99 tests
- `npm run test:contrast`: passed, 20 tests
- `npm run lint`: passed with 0 warnings after lint cleanup
- `npm ls` for remediated dependency paths: passed; Storybook's `giget` path resolves `tar@7.5.13 overridden`, and TypeScript ESLint resolves v8.59.1

## Outdated Result

`npm outdated --json` reports multiple frontend packages behind wanted/latest versions, including React, Vite, TypeScript ESLint, Storybook/Loki-related tooling, testing libraries, icons, animation, and visualization dependencies.

## Interpretation

The high-severity frontend dependency gate is closed for the current checkout. The dependency surface is not fully clean because low/moderate findings remain and several major upgrades are still available.

Do not claim dependency security is fully clean until all remaining audit findings are remediated or formally risk-accepted.
