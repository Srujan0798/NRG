# Docs Sync Issues - 2026-04-29

Status: resolved in current working tree.

## API Reference Drift

`docs/handover/API_REFERENCE.md` covers the core auth, `/query`, data, consent, audit, and health entry points, but it does not document every active endpoint in `src/api/main.py` and `src/api/routes/`.

Missing or under-documented endpoint groups:

- SSO: `/auth/sso/login`, `/auth/sso/callback`, `/auth/sso/status`
- Session lifecycle: `/auth/session`, `/auth/refresh`, `/auth/logout`
- Streaming query: `/api/query/stream`
- Telemetry and feedback: `/api/telemetry`, `/api/feedback`
- Health details: `/api/health/killer_queries`, `/health/llm`, `/api/providers/health`, `/health/db`, `/health/qdrant`, `/api/vectors/health`
- Ingest: `/api/ingest`, `/api/ingest/{job_id}`
- Metrics and operations: `/metrics`, `/api/metrics`, `/api/reindex`
- Admin RBAC: `/api/admin/rbac`, `/api/admin/rbac/{persona_name}`
- Graph internals: `/api/internal/tier_diff`
- Frontend fallback: `/{full_path:path}`

Resolution: `docs/handover/API_REFERENCE.md` now includes the endpoint groups above. A fresh endpoint coverage check found 58 runtime endpoints in `src/api/main.py` and 0 missing documented paths.

## Operations Runbook Drift

`docs/handover/OPERATIONS_RUNBOOK.md` references several script paths that are absent from the current tree:

- `scripts/backup.sh`
- `scripts/reimport_from_source.py`
- `scripts/regenerate_embeddings.py`
- `scripts/check_embedding_quality.py`
- `scripts/verify_query_quality.py`
- `scripts/investigate_audit.py`

Resolution: stale paths were replaced with existing scripts: `scripts/backup_db.sh`, `scripts/seed_from_csvs.py`, `scripts/ingest_qdrant.py`, `scripts/vector_drift_check.py`, `scripts/benchmark_dhairya_queries.py`, and `scripts/audit_investigate.py`.

## Data Intake Protocol Drift

`docs/handover/DATA_INTAKE_PROTOCOL.md` references absent helper scripts:

- `scripts/verify_intake_manifest.py`
- `scripts/scan_intake_pii.py`

Existing related scripts include:

- `scripts/ingest_qdrant.py`
- `scripts/verify_intake_bundle.py`
- `scripts/seed_production_tables.py`
- `scripts/benchmark_dhairya_queries.py`

Resolution: intake verification now references `scripts/verify_intake_bundle.py` and `scripts/data_quality_scorecard.py` with current argument names and environment-variable usage.

## Release Decision

Docs-sync is clean for the checked v1.0.0 handover API, operations, and data-intake surfaces. Evidence: `evidence/2026-04-28/docs_sync_report.txt`.
