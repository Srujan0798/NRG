# Frontend Dependency Gate

## Context

The May 2 frontend audit showed that high-severity findings can sit entirely
inside development tooling chains such as Storybook, TypeScript ESLint, Jest
environment dependencies, and transitive archive packages.

## Constraint

Treat `npm audit --audit-level=high` as a release gate, but do not claim full
dependency cleanliness while low or moderate findings remain. Patch-line and
targeted override fixes are acceptable only when they are verified by the
frontend build, Jest, lint, contrast/a11y checks, and dependency-tree evidence.

## Enforcement

For future frontend dependency work, capture before/after `npm audit` JSON,
`npm outdated`, `npm ls` for the vulnerable paths, and rerun `npm run build`,
`npm test -- --runInBand`, `npm run lint`, and relevant accessibility checks.
Document remaining low/moderate findings as remediation or formal
risk-acceptance work, not as a clean dependency surface.

## May 2 Loki Retirement

Unused visual-regression tooling can keep vulnerable transitive chains alive even
when the product no longer depends on it. Removing unused `loki` reduced the
frontend residual audit count from 25 moderate / 6 low to 18 moderate / 5 low
while preserving the high-severity gate, lint, build, Jest, and contrast checks.
Before deleting similar tooling, prove there are no package scripts, config
blocks, or source references left, then rerun the same frontend gate set.
