# NRG Quality Bar Scorecard — 2026-Q2

**Generated**: 2026-04-24
**Status**: 4/6 Passing | C4 (load test) and C5 (Qdrant) require infrastructure

## 6/6 Status

| # | Constraint | Score | Status |
|:--|:-----------|:-----:|:------:|
| C1 | DPDP-Compliant Indian PII Detection | 8/8 (100%) | ✅ PASS |
| C2 | Per-User Audit Binding (Non-Repudiation) | 26/26 (100%) | ✅ PASS |
| C3 | Multi-Hop Intent Decomposition (DAG Planner) | 24/24 (100%) | ✅ PASS |
| C4 | Production SLOs (P99 <500ms, ≥1000 concurrent) | SKIP | ⏭️ Unit tests pass; load test needs live API |
| C5 | Vector Drift Monitoring + Auto-Retrain Trigger | SKIP | ⏭️ Script runs; Qdrant required for full validation |
| C6 | Schema Allowlist Before Cloud LLM | 35/35 (100%) | ✅ PASS |

## Infrastructure Requirements to Achieve 6/6

- **C4**: Start API (`python -m uvicorn src.api.main:app`) + run locust `locust -f tests/load/locustfile.py --headless -u 1000 -r 100 --run-time 5m --host http://localhost:8000`
- **C5**: Start Qdrant (`docker compose up -d qdrant`) to enable vector drift cosine shift detection

## Run the Scorecard

```bash
python scripts/quality_bar_scorecard.py
```

## CI Enforcement

`.github/workflows/cd.yml` — `quality-bar` job blocks all deployments unless scorecard reports 6/6.
