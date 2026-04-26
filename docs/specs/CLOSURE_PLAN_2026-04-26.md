# NRG - Closure Plan 2026-04-26

**Status:** Production closure wave
**Authority:** `docs/specs/MASTER_EXECUTION_PLAN_2026-04-25.md`, `.claude/rules/production_only.md`, and active LB protocols `46..53`
**Scope:** Convert unsealed local work and cluster-bound acceptance into verifiable production state.
**External-audit merge:** Principal Auditor review 2026-04-26 is mapped in `.claude/memory/references/principal-auditor-2026-04-26.md`; Grok Principal Engineer review 2026-04-25 is mapped in `.claude/memory/references/grok-principal-engineer-2026-04-25.md`. They reinforce #56 through #60 and do not create a parallel source of truth.

## Current State

The repository has production-facing acceptance artifacts in place:

- `docs/operations/PRODUCTION_ACCEPTANCE_RUN.md`
- `scripts/seed_release_data.py`
- `evidence/2026-04-26/acceptance_run_recording.mp4`

The next gate is not more planning. The next gate is sealed evidence: committed slices, running-stack re-verification, full-suite proof, schema/RLS proof, anomaly-defense proof, and cluster activation.

## Gap Matrix

| ID | Gap | Bound To | Cluster-Only | Current State | Owner |
|---|---|---|---:|---|---|
| HYG-1 | Vocabulary purge and acceptance artifact cleanup | Production rule | No | Partially complete; verify grep and references | writer + founder |
| HYG-2 | Working-tree sealing by owner slice | Audit contract | No | Dirty tree; no claim counts until sealed by hash | active agents |
| LB-1 | Tier-shape filter at API response boundary | C2 | No | Needs committed code plus live curl proof | backend + security |
| LB-2 | Text-to-SQL hardening and adversarial suite | C3 | No | Needs committed prompt/code plus pytest proof | backend + ml |
| LB-3 | Three killer queries on seeded stack | C3 + C4-local | Partial | Needs p95 and cited rows against current HEAD | testing + data |
| LB-4 | Full pytest under 15 minutes | Gate | No | Needs current run, zero failures | testing + devops |
| LB-5 | Live red-team replay | C6 | No | Needs re-run after LB-1 seal | security |
| LB-6 | 58-table parity, indexes, RLS | C3 + Source #3 | No | Needs migration seal and live PG proof | backend + database |
| LB-7 | Result anomaly detector and answer confidence UI | C3 + Source #2 | No | Needs detector, pipeline, and UI proof | backend + ml + frontend |
| LB-8 | Semantic layer and schema-RAG | C3 + Sources #2/#3 | No | Needs integration proof and token reduction | backend + ml + data architecture |
| C4-CL | 1000-user load proof on sovereign cluster | C4 | Yes | Harness exists; cluster run pending | devops |
| C5-CL | Vector-drift baseline on populated Qdrant | C5 | Yes | Daemon exists; baseline pending | devops |
| GAP-D | Acceptance recording on sovereign staging | Handover | Yes | Capture script and acceptance runbook ready | devops |
| GAP-E | 600 GB PostgreSQL ingest | Handover | Yes | Data intake protocol ready | database |
| GAP-F | Three persona user-acceptance sessions | Handover | Yes | Scripts ready; scheduling pending | product |
| GAP-G | GPG signatures on handover docs | Handover | Founder key | Pending founder key/session | founder |
| GAP-H | Chain seal and attestation on live cluster | C1/C2/C6 | Yes | Test pack ready | security |

## Protocol Wave

| Protocol | Name | Done When | Depends On |
|---|---|---|---|
| #54 | Vocabulary Purge | Production vocabulary gate exits 0; CI job present; renamed artifacts have no stale references | None |
| #55 | Working-Tree Sealing | Owner-sliced commits exist for LB-1..LB-8 and BACKLOG rows carry commit hashes | #54 |
| #56 | LB-1..LB-5 Live Evidence | Running stack re-generates tier-shape, adversarial, killer-query, and red-team evidence against HEAD | #55 |
| #57 | LB-4 Full Suite | Canonical suite completes in under 15 minutes with zero failures and JUnit evidence | #55 |
| #58 | LB-6 Schema/RLS | 58/58 schema parity, RLS tier counts, and zero hot-join seq scans are evidenced | #55, #57 |
| #59 | LB-7 Confidence Defense | Anomaly detector covers 12+ signals; low-confidence answers retry or clarify; UI renders confidence | #55, #56, #58 |
| #60 | LB-8 Semantic Layer | Join graph covers 58 tables; schema retriever recall@5 >= 90%; prompt payload reduced >= 60% | #58 |
| #61 | Launch-Ready Seal | Local Quality Bar passes, production audit report is signed, and `v1.0.0-launch-ready` is tagged | #54..#60 |
| #62 | Sovereign Activation | Cluster load, drift baseline, ingest, user-acceptance sessions, chain seal, signatures, and `v1.0.0-eternal` are complete | #61 |

## Execution Order

1. Complete #54 and commit it first.
2. Seal owner slices under #55 without mixing unrelated LB work.
3. Re-run local live evidence under #56 and #57.
4. Verify database parity and semantic layers under #58..#60.
5. Produce the signed production audit and local tag under #61.
6. Move to cluster-bound activation under #62 only after #61 is sealed.

## Non-Negotiables

- No item is `DONE` without a commit hash and evidence path.
- Evidence must be regenerated against the current HEAD after code changes.
- The production vocabulary gate must pass before any sign-off.
- The master execution plan remains the source of truth; this plan is a closure overlay for #54..#62.

## Session-End Checklist

- BACKLOG has #54..#62 plus status and dependency rows.
- `.claude/memory/MEMORY.md` points at this closure plan.
- Three data sources are current: `db_struct.sql`, `tests/benchmarks/killer_queries.yaml`, and BACKLOG.
- Founder dependencies are explicit: DNS, SSO contract, GPG key, Langfuse keys, and cluster availability.
