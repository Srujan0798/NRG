# C4 Hot Path Hardening Summary - 2026-04-30

## Scope

This pass focused on the local C4 answer-engine path: startup responsiveness, auth/token overhead, query fast-path routing, audit behavior, hot-path logging, and 100-user Locust evidence.

## Changes Verified

- RSA private-key loading skips expensive validation after startup key files are trusted.
- Access-token verification reuses same-token/same-IP decoded claims while preserving replay detection for new IPs.
- Common C4 query shapes now route through bounded local fast paths instead of the slower workflow path.
- `/health` no longer blocks indefinitely on audit or Qdrant checks; slow dependencies return timeout/degraded status.
- High-volume request, PII redaction, training-capture, and blocked-prompt logs no longer flood the event loop by default.
- Blocking login/query/audit/workflow operations are moved off the async event loop.
- Audit singleton initialization is thread-safe under concurrent first use.
- Answer-record persistence is scheduled off the response path.

## Load Evidence

| Evidence path | Key result |
| --- | --- |
| `evidence/2026-04-30/live_c4_local_smoke_after_hotpath/locust_output.txt` | C4 failed; `/query` P99 about 10.8s. |
| `evidence/2026-04-30/live_c4_local_smoke_after_jwt_cache/locust_output.txt` | Login improved, but `/query` P99 still about 27.8s under load. |
| `evidence/2026-04-30/live_c4_local_smoke_after_logging_gate/locust_output.txt` | C4 failed; aggregate P99 about 20.5s. |
| `evidence/2026-04-30/live_c4_local_smoke_after_route_offload/locust_output.txt` | C4 failed; aggregate P99 about 8.8s. |
| `evidence/2026-04-30/live_c4_local_smoke_after_security_log_gate/locust_output.txt` | C4 failed; aggregate P99 about 6.0s. |
| `evidence/2026-04-30/live_c4_local_smoke_after_audit_init_fix/locust_output.txt` | Audit IDs were created under concurrency, but aggregate P99 regressed to about 28.9s because real audit writes were now on the path. |
| `evidence/2026-04-30/live_c4_local_smoke_after_worker_pool/locust_output.txt` | Best honest run in this pass: 0 failures, `/query` P99 about 7.4s, aggregate P99 about 6.4s. |

## Current Status

Superseded by `evidence/2026-04-30/c4_read_model_singleflight_closure.md`.

At the end of this earlier hot-path pass, C4 was not closed. The system was more correct and more stable, but the local single-process/PostgreSQL path still missed the stated `<500ms` P99 target under 100 users.

The remaining blocker is real hot-path data work under concurrency. Server logs during the final run show slow SQL on researcher ranking and count queries. The next pass should focus on precomputed read models or materialized views for the C4 query set, plus single-flight cache fill to stop concurrent cache misses from executing the same expensive SQL.

## Audit Verification

After the concurrent runs, audit-chain verification returned valid with zero errors:

```text
valid=True
error_count=0
valid_event_count=40524
```

## Recommended Next Step

This recommendation was implemented in the follow-up read-model/single-flight pass. The final passing local 100-user run is `evidence/2026-04-30/live_c4_local_smoke_after_read_model_final/locust_output.txt` with 8522 requests, 0 failures, aggregate P99 313.2ms, and `/query` P99 170ms.

Original recommendation: do not spend the next pass on more generic cleanup. Build a C4 read-model layer:

1. Precompute researcher rankings, state totals, institution counts, funding summaries, and common collaboration lists.
2. Route C4-shaped queries to read-model lookups only.
3. Add single-flight cache fill per normalized query/tier.
4. Keep audit IDs real, but move any non-essential persistence fully out of the response path.
5. Re-run the same `live_c4_local_smoke_after_worker_pool` profile and compare P50/P95/P99.
