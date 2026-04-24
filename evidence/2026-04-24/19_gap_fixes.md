# GAP Fix Evidence — 2026-04-24

## GAP-A — DB Co-Sign Module

- Status: FIXED-AND-VERIFIED locally; staging Postgres trigger application remains pending.
- Root cause: API-side audit binding existed, but the DB-side co-sign trigger/module was missing.
- Commit: `b873b713 [NRG-AUDIT-2026-04-24] audit — GAP-A — db_cosign Postgres trigger`
- Implementation:
  - `src/audit/db_cosign.py:31` defines `audit_cosign_trigger`, `audit_cosign_event`, and `db_cosign_hmac`.
  - `src/audit/db_cosign.py:82` adds `generate_audit_cosign_trigger_sql()`.
  - `alembic/versions/add_audit_cosign_trigger_001.py` applies the generated Postgres trigger DDL.
  - `src/migrations/versions/add_audit_cosign_trigger_001.py` mirrors the migration for the repo's migration layout.
- Before:
  - No `src/audit/db_cosign.py`.
  - No `audit_events.db_cosign_hmac`.
  - No `audit_cosign_trigger` in migrations.
- After:
  - DB co-sign HMAC is computed over `event_id:chain_hash:per_user_binding[:16]`.
  - Trigger writes `audit_events.db_cosign_hmac` on insert when `app.audit_db_cosign_key` is set.
- Verification:
  - `evidence/2026-04-24/05_audit_binding.log`
  - Result: `29 passed in 1.89s`.
  - `evidence/2026-04-24/gap_abc_verify.log` confirms local verifier status is `disabled:no_postgres_database_url`; the trigger must be applied against staging Postgres to produce live DB-side signatures.

## GAP-B — 60-Second Drift Scheduler

- Status: FIXED-AND-VERIFIED locally; long-running deployment unit/service remains staging work.
- Root cause: drift check existed, but no 60-second detect-to-emit scheduler existed.
- Commit: `527af236 [NRG-AUDIT-2026-04-24] observability — GAP-B — 60s drift scheduler`
- Implementation:
  - `scripts/vector_drift_scheduler.py:21` sets `DEFAULT_INTERVAL_SECONDS = 60`.
  - `scripts/vector_drift_scheduler.py:64` implements `should_trigger_reindex()`.
  - `scripts/vector_drift_scheduler.py:73` implements one scheduled pass.
  - `scripts/vector_drift_scheduler.py:92` implements the async scheduler loop.
- Before:
  - Drift checks were manual or cron-like, not a 60-second loop.
- After:
  - Scheduler dry-run reports interval 60 seconds, cosine shift threshold `0.05`, endpoint `/api/reindex`.
  - Unit tests mock the loop and verify the 60-second sleep and reindex trigger path.
- Verification:
  - `evidence/2026-04-24/20_vector_drift_scheduler.log`
  - Result: `4 passed in 6.31s`.
  - `evidence/2026-04-24/gap_abc_verify.log` dry-run reports `interval_seconds: 60`, `cosine_shift_threshold: 0.05`, `reindex_endpoint: /api/reindex`.

## GAP-C — Hall of Shame

- Status: FIXED-AND-VERIFIED.
- Root cause: `BACKLOG.md` and audit protocols referenced `src/data/schema/failed_queries/HALL_OF_SHAME.md`, but the file was missing.
- Commit: `4c743b84 [NRG-AUDIT-2026-04-24] docs — GAP-C — Hall of Shame seven patterns`
- Implementation:
  - `src/data/schema/failed_queries/HALL_OF_SHAME.md`
  - 195 lines covering all seven Dhairya failure patterns.
- Before:
  - `src/data/schema/failed_queries/HALL_OF_SHAME.md` did not exist.
- After:
  - File exists and documents P1 through P7 with original query, wrong SQL, failure reason, fix, and test coverage.
- Verification:
  - `wc -l src/data/schema/failed_queries/HALL_OF_SHAME.md` -> `195`.
  - `evidence/2026-04-24/gap_abc_verify.log`.

## Additional Security Closure

- Commits:
  - `b66d5ee0 [NRG-AUDIT-2026-04-24] security — red-team sanitizer hardening`
  - `bbe6102b [NRG-AUDIT-2026-04-24] security — close RT-18 and RT-19 red-team gaps`
- Evidence:
  - `evidence/2026-04-24/17_red_team_results.md`
  - RT-01 through RT-25 have zero ALLOWED security attacks after the patches.

## Remaining Non-Cluster Blockers Found During Verification

- Full suite is not green: `evidence/2026-04-24/01_pytest_full_suite.log`.
- Audit chain verification is currently not green: `evidence/2026-04-24/14_audit_chain_verify.log` reports one hash mismatch.
- Local load test is invalid: `evidence/2026-04-24/15_load_test_results.log` shows Locust task request-context errors before any HTTP request was made.
- Tier query JSON structures are not materially different across T1/T2/T3: `09_tier1_query_response.json`, `10_tier2_query_response.json`, `11_tier3_query_response.json`.
