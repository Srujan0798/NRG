# NRG Operations Runbook

## Vector Drift Scheduler

The vector drift scheduler enforces the C5 retrieval-quality guardrail.

- Local command: `python3 scripts/vector_drift_scheduler.py`
- Cron command: `python scripts/vector_drift_scheduler.py --once`
- Kubernetes manifest: `infrastructure/cron/nrg-drift-monitor/cronjob.yaml`
- Schedule: every minute (`* * * * *`) with `concurrencyPolicy: Forbid`
- Status file: `.cache/vector_drift_status.json` by default, or `NRG_VECTOR_DRIFT_STATUS_FILE`

On the first healthy run, the scheduler calls:

```bash
python scripts/vector_drift_check.py --establish-baseline --json
```

The baseline marker is written to `.cache/vector_drift_baseline.ok` by default, or
`NRG_VECTOR_DRIFT_BASELINE_MARKER` when set. When drift reaches `WARNING`,
`CRITICAL`, or cosine shift exceeds the configured threshold, the scheduler emits
a retrain/reindex event through `/api/reindex`.

The `/health` endpoint reports drift status under `vector_drift`, including the
latest `scheduler` marker when the scheduler has emitted one.

The cron manifest does not contain inline service credentials. Production
service tokens must be supplied through the `nrg-internal-service-token` Secret.

## Query Cache Pre-Warm

Before a production acceptance window, warm the query cache with the canonical
persona questions:

```bash
python3 scripts/prewarm_acceptance_cache.py --all
```

Default query cache TTL is `QUERY_RESULT_CACHE_TTL_SECONDS=300`. For extended
acceptance windows, raise the TTL through environment configuration and restart
the API workers.

## Local 100-User Load Evidence

Local load testing uses four API workers, trusted proxy headers for synthetic
client IP separation, Redis cache enabled, and the wider DB pool defaults:

```bash
UVICORN_WORKERS=4 \
DATABASE_POOL_MIN=20 \
DATABASE_POOL_MAX=40 \
QUERY_RESULT_CACHE_TTL_SECONDS=300 \
TRUST_PROXY_HEADERS=true \
python3 -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --workers 4
```

Run:

```bash
locust -f tests/load/locustfile_c4.py --headless --users 100 \
  --spawn-rate 25 --run-time 5m --host http://localhost:8000
```

Current evidence is stored in `evidence/2026-04-28/locust_100u_v2.json`. The
stale 90 percent failure mode is closed, but the corrected >50-QPS local profile
still fails because embedding models can lazily load inside the traffic window.
Preload or isolate embedding models before treating C4 as green.

## Data Quality Scorecard

The WE.6 scorecard checks seven data quality pillars: schema coverage,
referential integrity, null rate, freshness, completeness, consistency, and PII
sanitization.

- Local command: `python3 scripts/data_quality_scorecard.py`
- JSON output: `docs/ops/data_quality_scorecard.json`
- Markdown output: `docs/ops/data_quality_scorecard.md`
- Health signal: `/health` includes `data_quality`
- Grafana dashboard: `infrastructure/monitoring/dashboards/09_data_quality.json`
- P0 alerts: PII found in a non-PII table, or referential integrity below 90%

Weekly automation should run the scorecard against the representative database
and commit the refreshed JSON and Markdown outputs. Pre-commit runs the same
scorecard locally and blocks P0 regressions.

## Audit DB Co-Sign

DB co-signing is enabled only when `DATABASE_URL` points to PostgreSQL and
`AUDIT_DB_COSIGN_KEY` is set. Each audit append writes the chain event first,
then submits PostgreSQL co-sign work through the audit DB co-sign worker.

- Health signal: `/health` includes `audit.db_cosign`
- Metrics signal: `/api/metrics` includes `audit.db_cosign`
- Prometheus gauges: `nrg_audit_db_cosign_submitted`,
  `nrg_audit_db_cosign_succeeded`, `nrg_audit_db_cosign_failed`,
  `nrg_audit_db_cosign_queue_depth`, `nrg_audit_db_cosign_success_rate`, and
  `nrg_audit_db_cosign_latency_seconds`
- Verification command: `python3 -m pytest tests/audit/test_db_cosign.py tests/security/test_per_user_audit_binding.py --no-cov`

Failure modes:

- PostgreSQL unavailable during append: the chain append remains durable, the
  co-sign worker records a failed task, and a warning is logged.
- Missing DB co-sign row during verification: `verify_cosign()` returns
  `(False, None)`.
- Tampered co-sign row or tampered event fields: `verify_cosign()` returns
  `False` and logs a mismatch.
- Queue backlog: monitor `audit.db_cosign.queue_depth` and
  `nrg_audit_db_cosign_queue_depth`; sustained growth means the DB co-sign
  worker is not keeping up with audit write volume.

## TRL Safe View

The PostgreSQL source schema keeps the long table name
`innovations_at_various_stages_of_technology_readiness_level`. The production
database must also expose the short safe views created by
`alembic/versions/safe_trl_alias_views_001.py`:

- `trl_stages`
- `tech_trl_stages`

These views are a database-level guardrail for generated SQL. The
Text-to-SQL validator rejects identifiers over PostgreSQL's 63-byte limit before
execution, and generated TRL SQL should use the short view names.

Verification:

```bash
alembic upgrade head
psql "$DATABASE_URL" -c "\\dv trl_stages"
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM trl_stages"
```

Do not drop or rename the underlying long table. The safe view is an alias, not
a replacement table.

## Qdrant Empty Collection Guard

Qdrant vector retrieval is a hard dependency for RAG. If the active collection
has zero vectors, `/health` must report `retriever.status: critical`
when deep health checks are enabled, and Prometheus must fire
`QdrantCollectionEmpty` from `infrastructure/monitoring/alert-rules.yml`.

Operational rule: never deploy a release where `nrg_qdrant_vectors_total == 0`
unless the release is explicitly running in SQL-only maintenance mode. Some
small Qdrant collections legitimately report `indexed_vectors_count=0` while
`points_count>0`; use total points as the empty-collection signal.
