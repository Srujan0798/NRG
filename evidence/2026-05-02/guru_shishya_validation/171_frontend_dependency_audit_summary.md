# Frontend Dependency Audit Current Snapshot

Date: 2026-05-02

## Evidence

- `169_frontend_npm_audit_current.json`
- `170_frontend_npm_outdated_current.json`

## Current Audit Result

The current `npm audit` JSON reports 39 vulnerabilities:

- critical: 0
- high: 10
- moderate: 23
- low: 6

Dependency count from the audit metadata:

- production: 201
- development: 1167
- optional: 27
- total: 1368

## Current Outdated Result

`npm outdated --json` reports multiple frontend packages behind wanted/latest versions, including React, Vite, TypeScript ESLint, Storybook/Loki-related tooling, testing libraries, icons, animation, and visualization dependencies.

## Interpretation

This is not a runtime C4 blocker, but it remains a release/security gate. Several findings appear to sit under visual-regression/dev-tooling dependency chains, so remediation should be handled as a controlled frontend dependency upgrade with `npm run build`, frontend tests, Playwright/a11y checks, and screenshot evidence.

Do not claim dependency security is clean until `npm audit --audit-level=high` exits 0 or a formal risk-acceptance document explains the remaining high-severity dependency path.
