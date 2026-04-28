# Pipeline Contract Testing Protocol

WE.7 owns executable contracts for the six-node orchestration pipeline:

1. `receiver -> planner`
2. `planner -> router`
3. `router -> executor`
4. `executor -> synthesizer`
5. `synthesizer -> verifier`

Each edge contract is a JSON Schema in `src/orchestration/contracts/` with an
`x-contract-version` SemVer value. The validation command is:

```bash
python3 scripts/validate_contracts.py
```

## Required Gates

- Every schema must have a unique `$id`, valid SemVer version, and required fields.
- Producer tests must validate each node's emitted payload against the next edge schema.
- Consumer tests must validate each node accepts the prior edge payload and emits the next contract.
- `scripts/validate_contracts.py` must pass in pre-commit and CI.
- Generated docs must come from schemas, not hand-maintained copies:
  `docs/ops/pipeline_contracts.md`.

## SemVer Rules

- Patch bump: compatible clarification or description-only update.
- Minor bump: additive optional field.
- Major bump: removed field, renamed field, tightened type, stricter enum, or new required field.

Major contract bumps require integration tests for the pipeline and affected API
flows before merge. CI exposes `integration_required=true` when the current
schema major version exceeds the committed baseline in
`docs/ops/pipeline_contract_versions.json`.

## Contract Ownership

- `receiver_to_planner`: query identity and user context.
- `planner_to_router`: plan, desired skills, schema tables, domain context.
- `router_to_executor`: route, confidence, rationale, ambiguity, complexity.
- `executor_to_synthesizer`: evidence payload, execution timing, errors, warnings.
- `synthesizer_to_verifier`: response, citations, provenance, synthesis method.

Any change to a node input/output shape must update the corresponding schema and
its producer/consumer tests in the same change.
