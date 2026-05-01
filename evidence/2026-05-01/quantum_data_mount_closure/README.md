# Quantum Data Mount Closure - 2026-05-01

## Scope

The previous local warning closure proved the query path was stable, but the local Docker API still returned a cited no-result for `best quantum researchers....` because the API container only saw the compact `src/data/nrg_research.db`, whose `researchers` table was empty.

This pass wires the Docker development API to the populated local research corpus at `data/nrg_research.db` through a read-only mount. That makes the live local demo use real local corpus rows instead of an empty fallback database.

## Code Changes

- `docker-compose.yml`
  - Added `NRG_LOCAL_RESEARCH_DB=/app/data/nrg_research.db`.
  - Mounted `./data:/app/data:ro` into the API container.

- `tests/unit/test_compose_config.py`
  - Added a regression test proving the API service has the populated local DB env var and read-only data mount.

## Verification

| Check | Result | Evidence |
| --- | --- | --- |
| Compose contract | `6 passed` in `tests/unit/test_compose_config.py`; final targeted backend slice `46 passed` | `backend_regression.log` |
| Compose apply | API container recreated with the new env/volume | `docker_compose_up_api.log` |
| Live quantum data path | API resolves local research DB to `/app/data/nrg_research.db` | `live_quantum_query.json`, `live_query_matrix.json` |
| Quantum researcher rows | `717` rows match quantum through primary or secondary research-area fields | `live_quantum_query.json`, `live_query_matrix.json` |
| Researcher quantum query | `best quantum researchers....` returns `researcher_ranking`, 5 rows, 2 citations, audit ID | `live_query_matrix.json` |
| Tier 3 safety | `List top quantum computing researchers with emails` returns anonymized researcher labels, no direct email in answer, audit ID | `live_query_matrix.json` |
| PII/injection/out-of-corpus | Blocked or clarified with audit IDs | `live_query_matrix.json` |
| Health | `/health healthy`, `/health/all healthy` | `health.json`, `health_all.json` |
| Log scan | No `WARNING`, `ERROR`, `Traceback`, `HTTP 500`, or closed warning signatures in the captured post-mount window | `docker_logs_since_mount.log` |
| Corpus sync | `ok: true` | `corpus_sync.log` |
| Frontend build | passed | `frontend_build.log` |

## Honest Boundary

This closes the local Docker demo data-path gap for the quantum researcher query. It does not convert the ignored `data/nrg_research.db` into a tracked repository artifact, and it does not prove production/deployed data completeness. Production still needs its own populated database or an equivalent mounted/ingested corpus plus deployed replay evidence.
