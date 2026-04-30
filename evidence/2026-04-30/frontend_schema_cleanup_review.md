# Frontend And Schema Cleanup Review - 2026-04-30

## Restored From Cleanup Batch

The following staged deletions were restored because they are active source, active test dependencies, or unique project documentation:

- `frontend/src/components/ProofInspector/ProofInspector.tsx`
- `frontend/src/components/QueryWorkbench/QueryWorkbench.tsx`
- `frontend/src/components/SearchBar.tsx`
- `frontend/src/components/TierScopeBanner/TierScopeBanner.tsx`
- `frontend/src/components/WhatChangedAnnotation/WhatChangedAnnotation.tsx`
- architecture ADRs, data model, deployment guide, Phase 2 PRD, stakeholder deck, system architecture, ops runbooks, and project reports

## Kept As Cleanup

The remaining cleanup is intentionally narrow:

- `frontend/src/components/PersonaSheet/PersonaSheet.tsx`
  - No active source or test import remains. `PersonaToggle.tsx` now owns persona switching directly.
- `frontend/src/components/SearchBar.stories.tsx`
  - Storybook-only file with no active app or test dependency.
- `frontend/src/components/SideBySidePanel/SideBySidePanel.stories.tsx`
  - Storybook-only file with no active app or test dependency.
- `src/data/schema/optimized_schema.sql`
  - Verified identical to `src/data/schema/nrg_full_schema.sql`; active SQLite initialization uses `nrg_full_schema.sql`.

## Verification Plan

- `npm run build`
- focused component tests for `SearchBar`, `QueryWorkbench`, and `ProofInspector`
- `git diff --cached --check`
