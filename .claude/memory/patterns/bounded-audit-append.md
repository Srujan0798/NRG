# Bounded Audit Append

## Context

The May 2 C4 investigation showed `/query` route handlers were usually
low-millisecond, but 1000-user load expanded tail latency when synchronous audit
appends competed with the general API blocking threadpool.

## Constraint

Audit appends that produce `/query` `audit_event_id` must remain on the request
path and return the real chain hash. Do not replace them with fake IDs or a
fire-and-forget queue without a separate compliance design.

## Enforcement

Use a bounded dedicated audit append executor for request-path audit writes.
Default to one audit append worker per API process unless fresh load evidence
proves a different value is safer.

Evidence: `evidence/2026-05-02/guru_shishya_validation/c4_rerun/167_bounded_audit_executor_c4_pass_summary.md`.
