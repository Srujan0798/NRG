# C4 Load Test Report — NRG Eternal Seal Step 2

**Protocol**: #45 Eternal Seal
**Step**: 02_load
**Status**: PENDING_EXECUTION
**Date**: 2026-04-24
**Operator**: [Founder/DevOps]
**Cluster**: sovereign-staging

---

## Command Executed

```bash
kubectl port-forward svc/api 8000:8000 &
locust -f tests/load/locustfile.py --headless \
  --users 1000 --spawn-rate 50 --run-time 5m \
  --host https://api.nrg.internal --csv evidence/
```

## Results (Pending)

| Metric | Target | Observed | Pass/Fail |
|--------|--------|----------|-----------|
| P99 Latency | <500ms | TBD | ⏳ |
| P95 Latency | <300ms | TBD | ⏳ |
| P50 Latency | <100ms | TBD | ⏳ |
| Error Rate | <0.5% | TBD | ⏳ |
| Success Rate | >99.5% | TBD | ⏳ |
| Concurrent Users | ≥1000 | TBD | ⏳ |

## Percentile Distribution

```
Percentile | Latency (ms) | Status
----------|---------------|--------
50th (P50) | TBD | ⏳
75th (P75) | TBD | ⏳
90th (P90) | TBD | ⏳
95th (P95) | TBD | ⏳
99th (P99) | TBD | ⏳
99.9th     | TBD | ⏳
```

## Flame Graph

[Attach flame graph SVG from Locust]

## Scorecard Re-run

After load test completes:

```bash
kubectl -n nrg exec deploy/api -- python scripts/quality_bar_scorecard.py --emit-json
```

Expected: **6/6** (C4 flips ✅)

## Gate

- P99 < 500ms @ ≥1000 concurrent users → **C4 PASSES → QB 6/6**
- If fails: rollback, investigate, re-run

## Emit

- `docs/handover/evidence/02_load_report.md` (this file)
- `evidence/02_load_stats.csv` (Locust CSV output)
- Update Quality Bar Scorecard → 6/6
