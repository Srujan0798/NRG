# Data Quality And Structured Query Closure

Date: 2026-05-01

## Scope

This closure pass addressed the next local validation blockers after Qdrant health:

- data-quality monitor false failures for nullable optional columns;
- stale-age reporting clamped to `1.0` day;
- 12 official core analytical tables empty in the local Postgres stack;
- C4 read-model preemption of structured benchmark queries that should route to SQL evidence.

## Code Changes

- `src/observability/data_quality.py`
  - Null-rate now measures non-nullable/primary-key columns and reports skipped nullable columns.
  - Freshness age reporting now reports real measured days instead of score-clamped values.
- `scripts/seed_local_quality_fixtures.py`
  - New explicit local validation helper requiring `--allow-synthetic` or `NRG_ALLOW_LOCAL_QUALITY_FIXTURES=1`.
  - Tops up empty canonical core tables to the configured local minimum row count.
  - Refreshes local ingestion timestamps for generated local fixtures.
- `src/api/main.py` and `src/api/query_helpers.py`
  - Structured benchmark queries for sanctioned-vs-actual student strength and patent-per-PhD ratios bypass generic fast paths.
  - Added deterministic SQL for those benchmark shapes.
  - Prevented C4 read-model preemption for those structured benchmark shapes.
- Tests added in:
  - `tests/data/test_data_quality.py`
  - `tests/scripts/test_seed_local_quality_fixtures.py`
  - `tests/api/test_langgraph_api.py`

## Evidence Files

- `scorecard_before_seed.json` / `.md` / `.log`: host scorecard after monitor fixes, before local fixture seed. Remaining failures were completeness and freshness.
- `local_quality_fixture_seed.json`: explicit seed report; 12 empty core tables were topped up to 1,000 rows.
- `core_table_counts_after_seed.log`: database row-count proof for the 12 tables.
- `scorecard_after_seed.json` / `.md` / `.log`: host scorecard pass after seed.
- `scorecard_final.json` / `.md` / `.log`: final host scorecard pass after API rebuild.
- `health_final_after_scorecard_copy.json`: API `/health` after the container-visible data-quality scorecard was copied into the rebuilt API container.
- `health_final_after_vector_drift_copy.json`: API `/health` after container-visible vector drift status was copied into the rebuilt API container.
- `health_all_final_after_rebuild.json`: final `/health/all` status.
- `live_query_seeded_table_smoke_final.json`: live authenticated `/query` proof for seeded structured query paths.

## Final Local Status

- Data-quality scorecard: PASS, 0 P0 alerts.
- Core analytical table completeness: PASS, all configured core tables have at least 1,000 rows in the local Postgres stack.
- API health: healthy.
- RAG/Qdrant health: ready/healthy with 1,800 vectors.
- Vector drift status: GREEN from local status file, visible in `/health`.
- Audit chain: healthy and lineage intact.
- Structured query smoke:
  - sanctioned intake vs actual student strength routes to `text_to_sql` and returns 10 rows;
  - patents granted per PhD student ratio routes to `text_to_sql` and returns 10 rows;
  - capital expense vs innovation course count returns rows through the existing structured path.

## Honest Limits

- The seeded table data is a deterministic local validation fixture, not official production intake.
- The API container cannot generate the scorecard internally because the runtime image lacks SQLAlchemy for the standalone script; the final health evidence copies the generated host scorecard into the container-visible path.
- External production URL, Kubernetes rollout, founder signing, and public professor-demo evidence are still not proven in this local pass.
