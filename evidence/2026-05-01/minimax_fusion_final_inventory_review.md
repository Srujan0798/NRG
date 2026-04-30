# External Fusion Final Inventory Review

Date: 2026-05-01

## Answer

Before this pass, the external fusion was high-value but not inventory-complete.
The earlier evidence covered the highest-risk files and all five pasted prompt
inputs, but it did not explicitly account for every remaining source/config file
under `/Users/srujansai/Desktop/Minimax_mvp`.

This pass closes that accounting gap.

## Inventory

Fresh command:

```bash
find /Users/srujansai/Desktop/Minimax_mvp -path '*/node_modules' -prune -o -path '*/.git' -prune -o -type f -print
```

Result summary:

- All files found: 84
- Ignored as generated/binary/local artifacts: 27
  - `.DS_Store`: 5
  - `__pycache__`: 16
  - SQLite DB: 1
  - external audit chain file: 1
  - built `dist/` artifacts: 4
- Reviewable text files: 57

## Already Covered By Earlier Evidence

The earlier fusion passes covered:

- `nrg-frontend/src/pages/SearchPage.tsx`
- `nrg-frontend/src/layouts/DashboardLayout.tsx`
- `nrg-frontend/src/pages/LoginPage.tsx`
- `nrg-frontend/src/services/api.ts`
- `nrg-backend/src/api/main.py`
- `nrg-backend/src/api/models.py`
- `nrg-backend/src/skills/text_to_sql/sql_generator.py`
- `nrg-backend/src/security/security.py`
- all five files under `user_input_files/`

Evidence:

- `evidence/2026-04-30/minimax_fusion_acceptance.md`
- `evidence/2026-04-30/minimax_fusion_pass2_answer_context.md`
- `evidence/2026-05-01/minimax_fusion_pass3_query_validation.md`

## Newly Reviewed In This Pass

Frontend:

- `nrg-frontend/src/App.tsx`
- `nrg-frontend/src/components/ErrorBoundary.tsx`
- `nrg-frontend/src/contexts/AuthContext.tsx`
- `nrg-frontend/src/hooks/use-mobile.tsx`
- `nrg-frontend/src/index.css`
- `nrg-frontend/src/lib/utils.ts`
- `nrg-frontend/src/main.tsx`
- `nrg-frontend/src/pages/AnalyticsPage.tsx`
- `nrg-frontend/src/pages/PublicationsPage.tsx`
- `nrg-frontend/src/pages/ResearchersPage.tsx`
- `nrg-frontend/src/pages/SettingsPage.tsx`
- `nrg-frontend/src/types/index.ts`
- frontend package/config files by inventory review

Backend:

- `nrg-backend/src/audit/audit.py`
- `nrg-backend/src/auth/jwt_handler.py`
- `nrg-backend/src/db/database.py`
- `nrg-backend/src/db/seed.py`
- backend package/config files by inventory review

## Useful Value Extracted

| External source | Useful value | Decision | NRG target |
| --- | --- | --- | --- |
| `App.tsx` and `AuthContext.tsx` | Protected route/back-navigation/logout recovery checks | Convert to validation row | `W07` in validation matrix |
| `ErrorBoundary.tsx` | Need a safe error fallback, but external component exposes stack traces | Reject direct merge; convert to validation row | `U06` in validation matrix |
| `ResearchersPage.tsx` and `PublicationsPage.tsx` | Search/filter/modal interaction pattern for directories | Park as future directory UX only if backed by NRG API and tier proof | `U07` in validation matrix |
| `SettingsPage.tsx` | Privacy/access-log/deletion/2FA settings surface | Park as future settings contract; controls need real endpoints or disabled state | `U08` in validation matrix |
| `index.css` | Reduced-motion guard and skeleton pattern | Convert to UI/accessibility check; reject decorative visual system as direct merge | `U09` in validation matrix |
| `audit.py` | Simple audit-chain example | Reject direct merge; NRG audit chain is stronger and already canonical | Existing `src/audit/` |
| `jwt_handler.py` | Role/tier shape example | Reject direct merge due runtime secret, HS256, hardcoded users, and password bypass | Existing `src/auth/` |
| `database.py` and `seed.py` | Small SQLite schema and seeded rows | Reject direct merge because it conflicts with `db_struct.sql`, Dhairya, and current schema bridge | Existing `src/data/` and `db_struct.sql` |
| package/config files | Dependency and route context only | No direct merge | Existing NRG configs |

## Direct Merge Rejections

- Rejected frontend directory pages as-is because they use static data and can
  expose names/emails/phones outside the NRG evidence and tier pipeline.
- Rejected `ErrorBoundary.tsx` as-is because it renders stack traces to the
  user.
- Rejected external auth as-is because it uses a runtime-generated secret,
  HS256, hardcoded users, and test-password bypass behavior.
- Rejected external database/seed as-is because it is a small SQLite schema and
  does not preserve the official schema, Dhairya failure patterns, or current
  query contracts.
- Rejected the decorative CSS system as a direct style replacement because NRG
  already has a calmer answer-engine direction; kept reduced-motion/skeleton
  checks as useful validation.

## Matrix Update

`evidence/2026-05-01/external_fusion_validation_matrix.csv` was extended from
32 to 37 rows with:

- `W07` protected route/logout recovery
- `U06` safe error boundary
- `U07` directory filters with tier proof
- `U08` settings privacy controls
- `U09` reduced-motion and skeleton behavior

## Status

Inventory-complete external fusion accounting is now complete for the current
`/Users/srujansai/Desktop/Minimax_mvp` folder.

This does not mean direct merge of every file was appropriate. It means every
reviewable external file was either already covered, reviewed in this final
pass, ignored as generated/binary/local artifact, or rejected as an unsafe direct
merge with useful value converted where applicable.

## Remaining NRG System Blockers

Unchanged:

- deployed 1000-user cluster C4 proof
- deployed browser replay
- production Qdrant baseline
- founder signing
