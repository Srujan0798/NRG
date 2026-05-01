# Local Runtime Warning Closure - 2026-05-01

## Scope

This pass closed the local runtime warnings that were still visible after the post data-quality validation pass:

- `Answer record persistence failed`
- `Researcher ranking local catalogue fallback failed`
- `Final golden fast-path SQLite lookup failed`

It also keeps the previous safety boundary honest: this is a local product-path closure, not a production/cluster/founder-signing claim.

## Code Changes

- `src/services/answer_records.py`
  - Added `_default_answer_records_path()`.
  - The answer-record SQLite store now uses `NRG_ANSWER_RECORDS_DB` when configured, then writable `NRG_RUNTIME_DIR` or `/var/lib/nrg`, then local `data/answer_records.sqlite`.
  - This prevents the Docker API user from attempting to write answer records into a non-writable app source directory.

- `src/api/main.py` and `src/api/query_helpers.py`
  - Hardened local researcher fallback for sparse SQLite schemas.
  - The fallback now adapts to available researcher/institution columns instead of assuming legacy columns such as `department`, `secondary_research_areas`, `h_index`, and `total_funding_received_inr_crores`.
  - Optional local read-model probes now log schema misses at debug level instead of warning level because empty or compact local fallback DBs are expected in this environment.

- `tests/api/test_answer_records_api.py`
  - Added regression coverage for runtime-dir answer-record path selection.

- `tests/api/test_langgraph_api.py`
  - Added sparse local researcher catalogue regression coverage.
  - Added coverage that optional local SQLite schema misses do not produce warning-level log noise.

## Verification

| Check | Result | Evidence |
| --- | --- | --- |
| Backend regression slice | `78 passed, 38 deselected` | `backend_regression.log` |
| Docker API rebuild | passed | `docker_api_rebuild.log` |
| Live `/query` matrix | 8/8 HTTP 200, audit IDs present | `live_query_matrix.json` |
| Answer-record persistence | `/var/lib/nrg/answer_records.sqlite`, 18 records | `live_query_matrix.json` |
| Health | `/health healthy`, `/health/all healthy` | `health.json`, `health_all.json` |
| Final warning scan | no matching lines for closed warning/error signatures; no `WARNING`/`ERROR` lines in final captured window | `docker_logs_since_final_rebuild.log` |
| Corpus sync | `ok: true` | `corpus_sync.log` |
| Frontend build | passed | `frontend_build.log` |

## Live Matrix Notes

The final live matrix covered:

- capex vs innovation output
- noisy quantum researcher query
- state AI comparison
- government funding aggregate
- industry tier-safe researcher request
- PII block
- prompt-injection block
- out-of-corpus clarification

All returned HTTP 200 and carried audit IDs. Allowed evidence paths carried citations and source rows where rows exist. Blocked paths returned blocked envelopes with audit IDs.

## Honest Remaining Boundary

The local Docker/PostgreSQL/SQLite data currently contains zero quantum researcher rows:

- PostgreSQL query over `researchers`: `0`
- local SQLite fallback `researchers`: `0`

So `best quantum researchers....` now returns a cited, audited no-result response instead of a generic answer or fake ranking. To make that query produce real ranked people in the local live demo, the dataset must be seeded or ingested with verified quantum researcher records. The code path is covered by regression tests for real rows and sparse schemas; the remaining gap is data completeness, not a routing crash.
