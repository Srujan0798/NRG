---
name: Batch Gate Evidence Boundary
description: Batch task completion must distinguish local regression proof from external deployment, data-volume, cluster-load, and signing gates.
type: pattern
---

Context: Multi-batch closure work can produce strong local evidence while still
leaving sovereign-cluster, production-data, browser-deployed, or founder-signing
gates pending.

Constraint: Do not collapse `PASS locally`, `BLOCKED externally`, and
`UNKNOWN` into a single completion claim. A batch report must name the exact
command, evidence path, and missing environment input for each unresolved gate.

Enforcement mechanism: Batch handover docs should include a status matrix with
`PASS`, `FAIL`, `BLOCKED`, or `UNKNOWN`; external-gate scripts should return
`BLOCKED` with missing inputs instead of pretending the gate ran locally.
