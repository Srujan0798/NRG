# ADR-002: Query Helper Reconciliation

Date: 2026-05-05

## Status

Accepted.

## Context

Batch 1 identified that helper-looking query logic in `src/api/query_helpers.py`
could diverge from the live fast path previously embedded in `src/api/main.py`.
The behavioral delta matrix is preserved at
`evidence/2026-05-02/backend_query_reconcile/delta_matrix.md`.

After the answer-service extraction, the risk changed shape: the live query
contract now flows through `QueryAnswerService`, while `query_helpers.py`
remains a compatibility/helper module.

## Decision

The live query contract is:

1. public route tests;
2. `QueryAnswerService` behavior;
3. response-shape and tier-filter tests;
4. drift tests that compare helper behavior to the live contract.

`query_helpers.py` must not become a parallel answer implementation. Any helper
that changes response shape, audit event binding, tier filtering, fast-path
selection, or streaming timing must either delegate to the live service or add a
drift test that proves parity.

## Consequences

- Helper-only changes are not enough to change production query behavior.
- Response-shape changes require API tests and endpoint-matrix updates.
- Future reconciliation work should update the delta evidence before claiming a
  helper/main or helper/service divergence is closed.

## Verification

- `tests/api/test_query_helper_drift.py`
- `tests/api/test_query_response_shapes.py`
- `tests/api/test_query_service_extraction.py`
- `evidence/2026-05-02/backend_query_reconcile/delta_matrix.md`
- `evidence/2026-05-03/query_service_extraction/README.md`
