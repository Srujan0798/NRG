# Wave 5 Performance and Load Evidence

Date: 2026-04-30

## Scope

Wave 5 profiled the `/query` hot path under local concurrent TestClient load and ran the existing load-marked regression suites. The work focused on proven bottlenecks only:

- Optional cloud fast-path synthesis was allowed to hold deterministic responses for up to 30s.
- Audit append ordering could corrupt the HMAC chain under concurrent request bursts.
- Researcher lookup tried the wrong live schema first and repeated the same topic lookup across concurrent requests.
- Generic institution lookup missed the bounded local fast path.

This is local performance evidence. It is not a sovereign-cluster 1000-user C4 proof.

## Changes

- Reduced default optional fast-path AI synthesis timeout from 30s to 2s. If the model is slow, the API returns deterministic source-backed prose instead of blocking the answer.
- Serialized audit-chain appends with the in-process lock before acquiring the process file lock. This prevents concurrent local threads from corrupting the chain while preserving cross-process file locking.
- Reordered researcher lookup to try the live `researchers.institution` schema before the older `institution_id` join schema.
- Added a small researcher-topic cache so repeated concurrent topic lookups use the same verified rows instead of stampeding the database.
- Added institution lookup terms to the bounded local fast path.

## Local 100-Query Profile

Command shape:

```bash
NRG_QUOTA_DISABLED=1 CLOUD_SYNTHESIS_ALLOWED=false NRG_AI_SYNTHESIZE_FAST_PATHS=false \
.venv/bin/python <local TestClient 100 concurrent /query profile>
```

Evidence:

- Before optimization: `evidence/2026-04-30/wave5_local_100_query_profile_before.json`
- After audit/fast-path pass: `evidence/2026-04-30/wave5_local_100_query_profile_after_audit_fastpath.json`
- Final after audit rebuild and researcher-topic cache: `evidence/2026-04-30/wave5_local_100_query_profile_after.json`

| Run | Success | P50 | P95 | P99 | Throughput | Audit IDs |
|-----|---------|-----|-----|-----|------------|-----------|
| Before | 100/100 | 10089.34ms | 15688.97ms | 15854.71ms | 6.26 qps | FAIL |
| After audit/fast path | 100/100 | 3543.42ms | 6762.56ms | 7050.94ms | 14.01 qps | PASS |
| Final | 100/100 | 1613.59ms | 2031.49ms | 2094.72ms | 42.62 qps | PASS |

Final per-query P95:

- Highest computer science funding: 1863.22ms
- Best quantum researchers: 2161.80ms
- AI researchers in Gujarat: 2136.49ms
- IIT papers in 2024: 1761.82ms
- Institutions in Gujarat: 576.80ms

## Audit Chain Repair

The first pre-fix concurrent profile corrupted the live local `.audit/chain.jsonl`. The repo rebuild tool was used to preserve and rehash the chain:

```bash
.venv/bin/python scripts/audit_rebuild.py --rebuild --preserve-lineage
```

Result:

```text
Events processed: 38,301
Hashes corrected: 4,525
Corrupted chain backed up to: .audit/chain_corrupted_backup_20260430T013148Z.jsonl
Rebuild event logged with hash: 4c3a2170ed44433f674e...
```

Post-repair and post-final-profile verification:

```bash
.venv/bin/python scripts/audit_investigate.py
```

Result:

```json
{
  "ok": true,
  "events_checked": 38383,
  "broken_indices": []
}
```

## Tests Run

```bash
.venv/bin/python -m pytest tests/api/test_ai_synthesis.py::test_ai_synthesis_default_timeout_is_short_for_fast_paths -q
```

Result:

```text
1 passed in 2.38s
```

```bash
.venv/bin/python -m pytest tests/api/test_k4_publication_count_fast_path.py tests/api/test_langgraph_api.py::test_unsupported_ranked_researcher_topic_clarifies_instead_of_generic_fast_path tests/api/test_ai_synthesis.py tests/audit/test_chain_integrity.py::TestAuditChainIntegrity::test_concurrent_appends -q
```

Result:

```text
9 passed in 2.66s
```

```bash
.venv/bin/python -m pytest tests/performance/test_query_latency_hot_path.py -q -m load
```

Result:

```text
7 passed in 1.53s
```

```bash
SLO_ENV=prod .venv/bin/python -m pytest tests/load/test_slo_under_load.py -q -m load
```

Result:

```text
5 passed in 11.67s
```

```bash
.venv/bin/python -m pytest tests/load/test_concurrent_queries.py -q -m load
```

Result:

```text
6 passed in 13.48s
```

## Acceptance Status

| Requirement | Status |
|-------------|--------|
| Profile `/query` under concurrent load | PASS |
| Identify top latency sources | PASS |
| Optimize only proven bottlenecks | PASS |
| Fresh load report | PASS |
| P95/P99 and failure rate reported | PASS |
| 100-user load evidence | LOCAL PASS |
| C4 production/cluster proof | BLOCKED |

## Live Local Locust Smoke

After the live quantum browser/API proof, a bounded local C4-style Locust smoke was run against a live backend on `127.0.0.1:8020`.

Evidence:

- `evidence/2026-04-30/live_c4_local_smoke/README.md`
- `evidence/2026-04-30/live_c4_local_smoke/locust_stats.csv`
- `evidence/2026-04-30/live_c4_local_smoke/locust_report.html`
- `evidence/2026-04-30/live_c4_local_smoke/health_before.json`
- `evidence/2026-04-30/live_c4_local_smoke/health_after.json`

Result:

| Run | Users | Duration | Requests | Failures | Query P95 | Query P99 | Status |
|-----|-------|----------|----------|----------|-----------|-----------|--------|
| Local Locust smoke | 100 | 60s | 3602 | 0 | 2300ms | 2700ms | STABLE, C4 latency FAIL |

Post-run audit verification:

```json
{
  "ok": true,
  "events_checked": 39036,
  "broken_indices": []
}
```

## Remaining Blocker

C4 is improved but not closed. The local 100-query TestClient profile had P99 2094.72ms, and the live local 100-user Locust smoke had query P99 2700ms with zero failures. Both are above the strict 500ms target noted in `tests/load/locustfile_c4.py`. A true C4 closure still requires a running deployment and Locust run against the cluster or local service:

```bash
python scripts/run_load_test.py --host http://localhost:8000 --users 1000
```

Do not claim full C4 production readiness until that run passes or the official C4 threshold is clarified.
