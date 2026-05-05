# Specs ADR Index

This folder contains specs-facing ADRs for Batch 7 handover. Implementation ADRs
that already existed under `docs/adr/` remain valid; entries here make the
source-of-truth decision points discoverable from `docs/specs/`.

| ADR | Status | Decision |
|---|---:|---|
| [ADR-001 Main.py Answer-Engine Split](ADR-001-main-py-answer-engine-split.md) | Accepted | Keep `src/api/main.py` as app wiring and move live query behavior behind `QueryAnswerService`. |
| [ADR-002 Query Helper Reconciliation](ADR-002-query-helper-reconciliation.md) | Accepted | Treat `QueryAnswerService` and route tests as the live contract; `query_helpers.py` is compatibility/helper code only. |
