# Vector Drift Runtime Evidence

Date: 2026-04-25  
Qdrant runtime: direct Docker container `nrg-qdrant-temp` on `127.0.0.1:6333`

## Commands Run

```bash
docker run -d --name nrg-qdrant-temp -p 6333:6333 -p 6334:6334 qdrant/qdrant:v1.11.3
.venv/bin/python scripts/init_qdrant.py
.venv/bin/python -c 'from scripts.insert_test_data import insert_qdrant_test_data; insert_qdrant_test_data()'
curl -X PATCH http://127.0.0.1:6333/collections/nrg_research \
  -H 'Content-Type: application/json' \
  -d '{"optimizers_config":{"indexing_threshold":1}}'
.venv/bin/python scripts/vector_drift_check.py --check-only --json
.venv/bin/python scripts/vector_drift_check.py --json
```

## Health Check

```json
{
  "qdrant": {
    "indexed_vectors": 128,
    "total_vectors": 128,
    "coverage_pct": 100.0,
    "status": "ok",
    "latency_ms": 40.63
  }
}
```

## Drift Benchmark

The benchmark ran all 10 queries against live Qdrant and exited non-zero because drift was critical:

```text
Drift Score: 0.013
Alert Level: CRITICAL
Queries: 10
SLO Target: >=0.85
WARNING: <0.60
CRITICAL: <0.40
```

This result is expected for the local random-vector seed set. It proves the detector is operational and fails closed when retrieval content does not match the benchmark expectations.

## Fixes Made

- `scripts/insert_test_data.py`: removed unsupported `QdrantClient(check_compatibility=False)` argument for the installed client version.
- `scripts/insert_test_data.py`: increased test-vector seed volume from 10 to 128 points so local HNSW indexing can be exercised.
- `scripts/vector_drift_scheduler.py`: reused the drift checker readiness gate so the scheduler does not start expensive benchmark runs when Qdrant is empty or unindexed.

## Residual Risk

This is not a production-quality drift baseline because the seeded vectors are synthetic/random. A production baseline still requires domain-real documents indexed into Qdrant, then a fresh run where `drift_score >= 0.85`.
