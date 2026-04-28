# Docs Sync Report

**Date:** 2026-04-28
**Scope:** `docs/handover/` compared with `src/api/`, `src/api/routes/`, and `scripts/`.

## Summary

Mismatches found. The handover packet remains usable for review, but the listed items should be corrected before final packaging.

## API Reference vs Code

| Finding | Evidence | Action |
|---|---|---|
| API reference documents the core login/query/data/DPDP/audit/health flows, but not all implemented routes. | `src/api/main.py` and route modules expose additional endpoints including `/auth/sso/*`, `/api/query/stream`, `/api/telemetry`, `/api/health/killer_queries`, `/api/providers/health`, `/api/vectors/health`, `/api/feedback`, `/api/ingest`, `/api/reindex`, `/api/admin/rbac`, `/admin/slo`, `/metrics`, and several direct data endpoints. | Expand `docs/handover/API_REFERENCE.md` or move internal/admin endpoints to an operator-only API appendix. |
| API reference includes a citation detail request for `/publications/pub_001`, but no matching implemented route was found. | Route scan shows `GET /publications` only, not `GET /publications/{id}`. | Either add the route or remove the citation detail command from the docs. |
| API reference describes a WebSocket query path, but no WebSocket route was found in `src/`. | `rg "WebSocket|@app.websocket|/ws/query" src` found no API route. | Replace with the implemented `/api/query/stream` HTTP streaming endpoint or add a WebSocket route. |

## Operations Runbook vs Scripts

| Finding | Evidence | Action |
|---|---|---|
| Backup cron points to `/opt/nrg/scripts/backup.sh`, but the repo has `scripts/backup_db.sh` and `scripts/backup_nrg.sh`. | `scripts/backup.sh` is absent. | Update the runbook to the intended backup script. |
| Embedding recovery section references `scripts/regenerate_embeddings.py`, which is absent. | Available related scripts include `scripts/build_embeddings.py`, `scripts/ingest_qdrant.py`, and `scripts/ingestion/*`. | Update the runbook to the current embedding/index rebuild path. |
| Embedding quality section references `scripts/check_embedding_quality.py`, which is absent. | No matching script exists. | Add the checker or document the current vector validation command. |
| Query quality verification references `scripts/verify_query_quality.py`, which is absent. | Available alternatives include `scripts/capture_killer_query_evidence.py`, `scripts/benchmark_dhairya_queries.py`, and benchmark tests. | Update the runbook to the current validation command. |
| Audit investigation section references `scripts/investigate_audit.py`, but the repo has `scripts/audit_investigate.py`. | `scripts/investigate_audit.py` is absent; `scripts/audit_investigate.py` exists. | Rename the command in the runbook. |

## Data Intake Protocol vs Scripts

| Finding | Evidence | Action |
|---|---|---|
| Handover protocol references `scripts/verify_intake_manifest.py`, but the current verifier is `scripts/verify_intake_bundle.py`. | `scripts/verify_intake_manifest.py` is absent; `scripts/verify_intake_bundle.py` exists and checks manifest, GPG sidecars, and row HMAC. | Update the protocol command to `scripts/verify_intake_bundle.py`. |
| Handover protocol references `scripts/scan_intake_pii.py`, but no matching script exists. | No script with that path exists under `scripts/`. | Add the PII scanner or document the current security scan command. |
| HMAC environment variable name differs between docs and code. | The handover protocol uses `HMAC_SECRET_KEY`; `scripts/verify_intake_bundle.py` defaults to `DATA_INTAKE_HMAC_SECRET`. | Standardize docs on `DATA_INTAKE_HMAC_SECRET` or add compatibility support. |
| Full protocol cross-reference exists. | `docs/DATA_INTAKE_PROTOCOL.md` is present. | No action required. |

## Conclusion

Docs and code are not fully synchronized. The highest-priority fixes are the missing intake command names, missing WebSocket route documentation alignment, and absent runbook helper scripts.
