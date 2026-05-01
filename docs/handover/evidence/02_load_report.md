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
KUBECONFIG=/path/to/sovereign-cluster \
.venv/bin/python scripts/run_final_external_gates.py \
  --evidence-dir evidence/$(date +%F)/final_external_gates \
  --run-cluster-load
```

The runner invokes `tests/load/run-locust-k8s.sh production` after verifying cluster access.

## Results (Pending)

| Metric | Target | Observed | Pass/Fail |
|--------|--------|----------|-----------|
| P50 Latency | <500ms | TBD | ⏳ |
| P99 Latency | <3s | TBD | ⏳ |
| Error Rate | <1% | TBD | ⏳ |
| Throughput | ≥100 RPS | TBD | ⏳ |
| Success Rate | >99% | TBD | ⏳ |
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
kubectl -n nrg exec deploy/api -- python scripts/quality_bar_scorecard.py --json-only
```

Expected: **6/6** (C4 flips ✅ → C4: 1/1 PASS)

## Gate

- P50 < 500ms, P99 < 3s, error < 1%, throughput ≥100 RPS @ ≥1000 concurrent users → **C4 PASSES**
- If fails: rollback, investigate, re-run

## Emit

- `docs/handover/evidence/02_load_report.md` (this file — fill observed values)
- `evidence/02_load_stats.csv` (Locust CSV output)
- Update `scripts/quality_bar_scorecard.json` → overall: "6/6", is_6_6: true
