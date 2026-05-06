# C4 P99 Optimization - Blockers

**Date:** 2026-05-06
**Status:** BLOCKED after 3 optimization attempts

## Stop Rule Triggered

The assignment says to stop if P99 does not drop below the gate after 3 optimization attempts. That condition is met.

Latest measured C4 result:

- P99: `21000ms`
- P95: `3700ms`
- Mean: `1481ms`
- Failure rate: `1.51%`
- Samples: `118,788`
- Target: P99 `<500ms`, failure rate `0%`

## What Remains Blocked

1. C4 requires either a materialized/read-only load-test path that is part of the product contract, or a deeper runtime redesign. The retained prompt-block cache is safe, but not enough.
2. Local Docker plus Locust plus FastAPI on this laptop is producing HTTP 0 failures and long queue tails at 1000 users. That is not a clean production proof.
3. C5 timed out in two later scorecard attempts, so the latest scorecard is `4/6`, not `5/6` or `6/6`.
4. Any further C4 work should start from a dedicated profiling run with API process metrics, Locust worker metrics, Docker memory/CPU, and PostgreSQL/Qdrant metrics captured together.

## Recommended Next Step

Escalate to Guru with the failed evidence and decide whether the C4 target is meant to be:

- a local laptop proof,
- a cluster proof,
- or a product SLO backed by a specific read model/cache contract.

Do not claim C4 pass until the full `NRG_C4_REQUIRE_LIVE=1 .venv/bin/python scripts/quality_bar_scorecard.py` run reports C4 PASS with P99 `<500ms` and `0` failures.
