# ADR-008: Query Helper Reconciliation

Date: 2026-05-05

## Status

Accepted for local source-truth discipline.

## Context

The May 2 80-task dispatch plan flagged a risk that `src/api/main.py` fast-path
query behavior could diverge from `src/api/query_helpers.py`. That risk matters
because NRG responses must preserve the public answer contract: audit event ID,
tier-aware shape, citations or source rows when applicable, and safe blocked
envelopes for adversarial or PII requests.

On May 3 the live `/query` and `/api/query/stream` bodies moved behind
`QueryAnswerService` in `src/api/query_service.py`. ADR-007 records that split.
The helper reconciliation decision below preserves the same source-of-truth
rule for future changes.

## Decision

`QueryAnswerService` is the behavioral authority for query execution.

`src/api/query_helpers.py` may keep compatibility helpers, but helper functions
must not become an independent query implementation. Any helper that shapes,
blocks, fast-paths, or normalizes query responses must either:

- delegate to the live service path or shared response-contract utility; or
- have drift tests proving it produces the same externally visible contract as
  the live route for the covered case.

New query fast paths belong in the service layer or in injected dependencies
owned by the service, not in `main.py` or parallel helper-only code.

## Consequences

- Route files stay thin and focused on HTTP wiring.
- Helper modules remain safe to import without becoming shadow behavior owners.
- Any future query-helper edit must include either a drift test or an explicit
  note that it is a pure utility with no response-contract authority.
- Evidence for query-helper reconciliation is local unless replayed against a
  deployed API target.

## Verification

- `evidence/2026-05-03/l1_query_helper_drift_closure/README.md`
- `evidence/2026-05-03/query_service_extraction/README.md`
- `tests/api/test_query_helper_drift.py`
- `tests/api/test_query_service_extraction.py`
