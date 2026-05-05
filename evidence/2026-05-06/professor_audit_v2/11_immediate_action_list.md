# Immediate Action List — Professor Audit v2

## Next 24 Hours

| # | Action | Owner | Evidence Path |
|---|--------|-------|---------------|
| 1 | Commit all evidence files to git | Srujan | `git add evidence/2026-05-06/professor_audit_v2/` |
| 2 | Run `npm run build` in frontend/ | Srujan | Verify `frontend/dist/` created |
| 3 | Check seed data migration script | Srujan | Look for `scripts/migrate_seed_data.py` or similar |

## Next 48 Hours

| # | Action | Owner | Evidence Path |
|---|--------|-------|---------------|
| 4 | Fix bundle size — replace recharts or configure Vite manualChunks | Srujan | Rebuild must show < 250KB |
| 5 | Run live C4 load test — verify P99 < 500ms @ 1000 concurrent | Srujan | `NRG_C4_API_BASE_URL` + `NRG_C4_REQUIRE_LIVE=1` |
| 6 | Document Qdrant setup or fix C5 vector drift check | Srujan | `scripts/vector_drift_check.py` exit 0 |

## Before Any Funding Discussion

| # | Action | Owner | Blocker |
|---|--------|-------|---------|
| 7 | Deploy staging URL (cloud/K8s/Docker) | Srujan | **CRITICAL** |
| 8 | Migrate seed data to PostgreSQL | Srujan | **CRITICAL** |
| 9 | Verify killer queries return rows (not 0) on live API | Srujan | **CRITICAL** |
| 10 | Schedule founder GPG signing ceremony | Srujan | **HIGH** |

## Before Professor Walkthrough

| # | Action | Owner | Verification |
|---|--------|-------|-------------|
| 11 | Production build verified (dist/ exists, bundle < 250KB) | Srujan | `ls frontend/dist/` + chunk size check |
| 12 | End-to-end test: login → query → answer on staging URL | Srujan | Playwright or manual |
| 13 | Prepare demo script that avoids all blocked features | Srujan | Demo script in evidence/ |

---

*Last updated: 2026-05-06*