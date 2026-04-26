# Production Web App Status — 2026-04-27

## Scope

This report covers the production web application hardening completed locally on 2026-04-27. It records code changes and reproducible evidence from this workspace. It does not claim sovereign-cluster acceptance, physical-device certification, or 600GB production-data acceptance because those were not available locally.

## What Was Added Or Fixed

1. **Authenticated production workspace screens**
   - Added first-class routes for:
     - `/app/publications`
     - `/app/researchers`
     - `/app/reports`
     - `/app/industry`
     - `/app/settings`
   - Files:
     - `frontend/src/pages/ProductionWorkspace.tsx`
     - `frontend/src/pages/productionWorkspaceConfig.ts`
     - `frontend/src/pages/productionWorkspaceData.ts`
     - `frontend/src/App.tsx`

2. **Role-aware access boundaries**
   - Tier 1 can open researcher profiles.
   - Tier 2 can open government reports and aggregate views.
   - Tier 3 navigation only advertises allowed sections and the industry view uses aggregate data only.
   - Direct access to restricted routes renders a professional restricted-state panel and does not render PII rows.

3. **Production support screens backed by live APIs**
   - Publications explorer reads `/publications`.
   - Researcher profiles read `/researchers` for Tier 1 only.
   - Government reports read `/stats`.
   - Industry capability reads `/stats` and renders anonymized aggregate capability rows.
   - Settings reads `/audit/events` through `queryService.listAuditEvents`.

4. **Backend `/researchers` schema-drift fix**
   - File: `src/data/database_v2.py`
   - The ORM path now falls back to a schema-inspected raw SQL path when a deployed database lacks newer ORM columns such as `institution_id`.
   - This fixes the live crash observed while exercising `/app/researchers`.

5. **Repository tracking cleanup**
   - `.gitignore` now ignores only the root `/data/` directory instead of every path named `data`.
   - Required source files under `src/data/` and `tests/data/` are now tracked so a fresh clone has the backend modules imported by `src/api/main.py` and Alembic.

6. **Frontend stability hardening**
   - Production workspace tests verify route coverage, Tier 3 PII blocking, role-aware navigation, and compact metric parsing.
   - The industry screen no longer depends on a natural-language query call for shell data, removing a brittle failure path.
   - Aggregate screens render truthful fallback rows from live totals instead of blank panels when distributions are not present.

## Evidence

Frontend evidence:

- `docs/audits/frontend_production_app_2026-04-27/frontend-tests.log`
  - `19 passed, 19 total`
  - `71 passed, 71 total`
- `docs/audits/frontend_production_app_2026-04-27/frontend-build.log`
  - Vite production build passed.
- `docs/audits/frontend_production_app_2026-04-27/frontend-lint.log`
  - ESLint passed with no warnings.

Backend evidence:

- `evidence/2026-04-27/researchers_schema_drift_regression.log`
  - `tests/data/test_database_v2_schema_drift.py` passed.
- `evidence/2026-04-27/researchers_endpoint_schema_drift_live.txt`
  - Live Tier 1 `GET /researchers?limit=3` returned HTTP 200.
- `evidence/2026-04-27/tier3_researchers_pii_guard_live.txt`
  - Live Tier 3 `GET /researchers?limit=3` returned anonymized aggregates.
- `evidence/2026-04-27/tier3_researchers_pii_guard_assertion.log`
  - Assertion passed: no `email`, `phone`, `name`, or `@` token in the Tier 3 response.

Screenshots:

- `docs/audits/frontend_production_app_2026-04-27/screenshots/01_login_desktop.png`
- `docs/audits/frontend_production_app_2026-04-27/screenshots/01_login_mobile.png`
- `docs/audits/frontend_production_app_2026-04-27/screenshots/02_publications_desktop.png`
- `docs/audits/frontend_production_app_2026-04-27/screenshots/02_publications_mobile.png`
- `docs/audits/frontend_production_app_2026-04-27/screenshots/03_researchers_desktop.png`
- `docs/audits/frontend_production_app_2026-04-27/screenshots/03_researchers_mobile.png`
- `docs/audits/frontend_production_app_2026-04-27/screenshots/04_reports_desktop.png`
- `docs/audits/frontend_production_app_2026-04-27/screenshots/04_reports_mobile.png`
- `docs/audits/frontend_production_app_2026-04-27/screenshots/05_industry_desktop.png`
- `docs/audits/frontend_production_app_2026-04-27/screenshots/05_industry_mobile.png`
- `docs/audits/frontend_production_app_2026-04-27/screenshots/06_settings_desktop.png`
- `docs/audits/frontend_production_app_2026-04-27/screenshots/06_settings_mobile.png`

Production walkthrough video files:

- `docs/audits/frontend_production_app_2026-04-27/videos/`

## Remaining Blockers

- Real iOS and Android physical-device checks were not available in this local run.
- Sovereign-cluster `docker compose up` replacement validation and 600GB production data loading were not available in this workspace.
- C4 at 1000 concurrent users remains a cluster-only acceptance gate.

## Status

The local full-stack application now has authenticated production support screens beyond the front page, role-aware navigation, live API-backed table views, Tier 3 PII guard evidence, a repaired `/researchers` endpoint, screenshots, video evidence, and green frontend/backend targeted checks.
