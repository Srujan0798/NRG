# Local Release Gates — 2026-04-27

This evidence records what was fixed and verified locally on 2026-04-27. It does not claim sovereign-cluster C4 approval or real 600GB data acceptance.

## Code Changes

1. Audit DB co-sign scheduling now runs only for PostgreSQL targets with `AUDIT_DB_COSIGN_KEY`.
2. Audit DB co-sign uses a bounded worker pool instead of spawning a daemon thread per audit event.
3. Audit append hot-path logging was reduced from `INFO` to `DEBUG`.
4. C4 Locust profile now authenticates with current credentials and validates the live API response shape.
5. C4 Locust profile stops unauthenticated users cleanly with `StopUser`.
6. Load tests now force mocked/local LLM behavior and patch verifier LLM access, so load gates do not call real providers.

## Verification Commands

```bash
PYTEST_ADDOPTS=--no-cov .venv/bin/pytest \
  tests/audit/test_db_cosign.py \
  tests/config/test_locustfile_contract.py \
  tests/observability/test_vector_drift.py \
  tests/observability/test_vector_drift_scheduler.py \
  -q
# 40 passed in 0.71s
```

```bash
PYTEST_ADDOPTS=--no-cov SLO_ENV=prod .venv/bin/pytest tests/load -m load -q --tb=short
# 17 passed in 32.51s
```

```bash
.venv/bin/python -m py_compile tests/load/locustfile_c4.py
# pass
```

```bash
.venv/bin/python scripts/vector_drift_check.py --json --check-only
# qdrant.status = unhealthy locally, indexed_vectors = 0, total_vectors = 0
```

## Remaining Non-Local Gates

| Gate | Why It Cannot Be Closed Locally |
|------|---------------------------------|
| Sovereign C4 P99 at 1000 users | Requires Kubernetes/HPA and production-like infrastructure. A MacBook Locust run is not valid evidence. |
| Vector drift runtime pass | Requires a live Qdrant `nrg_research` collection with indexed vectors. Local health currently reports 0 vectors. |
| 600GB production data acceptance | Requires ministry/DPDP data transfer and ingestion approval. |
| UAT sessions | Requires scheduled Researcher, Government, and Industry evaluators. |
| Founder GPG signatures | Requires founder key ceremony and signing authority. |

## Status

The locally fixable code gates are closed. The remaining acceptance gates are infrastructure, data, and stakeholder gates that must be executed in the production or sovereign staging environment.
