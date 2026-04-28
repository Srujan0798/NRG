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
