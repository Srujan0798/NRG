# v1.0.0 - Sovereign Launch

This changelog summarizes the local handover state through `6085c3b`. Cluster-gated validation, founder signatures, and commercial gates remain outside this local engineering packet.

## Features

- Split the FastAPI surface into modular route slices for auth, data, graph, health, ingest, query, and admin flows (`7fe47b3`).
- Added SQL-only fast-path synthesis, query plan caching, and latency hot-path coverage (`bccc061`).
- Added the `trl_stages` database view and canonical schema alias coverage for the long TRL source table (`964c2bb`, `0463f39`, `4bf6bd6`).
- Added SSO endpoints, DPDP consent/export/erase flows, and production schema guardrails (`0dc388d`, `454f332`).
- Added Tier 1, Tier 2, and Tier 3 UAT query sets for handover sessions (`95f4199`).
- Added governance monitor, quality-gate artifacts, and Phase 2 sprint planning docs (`32398c3`).

## Security

- Added Qdrant zero-vector CRITICAL health behavior and regression coverage (`e03b081`, `6100a25`, `f2208f9`).
- Added ADR-006 genesis hash pinning, `lineage_intact`, and audit-chain health behavior (`e727d54`).
- Purged production-forbidden vocabulary from active paths and recorded full-repo vocabulary evidence (`0fa298a`, `0a3d602`, `c11bc15`).
- Fixed consent banner behavior, tier response filtering, PII injection handling, and citation-presence tests (`454f332`, `6085c3b`).
- Added final local code-review blockers and security evidence mapping for handover review (`622217b`, `b0f6dba`).

## Performance

- Added K-4 cold-query latency evidence and publication-count cache warm path (`26f4e77`, `c38421a`).
- Added 100-user K-2 load-test evidence and incident follow-up for the remaining C4 latency blocker (`14d23db`).
- Added vector-drift scheduler evidence and quality-bar scorecard updates (`1f0be5f`).
- Added query plan cache reuse coverage and LLM timeout fallback coverage for the Text-to-SQL hot path (`bccc061`).

## Fixes

- Fixed schema parity and RLS-related tests, including rate-limit handling in tier-isolation tests (`692c2ed`).
- Fixed health endpoint table counts, prompt sanitiser encoding, and query response evidence generation (`2743379`, `6085c3b`).
- Fixed citation presence test patching and workflow dependency mocking (`6085c3b`).
- Fixed active-path production naming and acceptance-script references (`cabc4be`, `c11bc15`).

## Operations

- Added handover manifest, final checklist, and evidence cross-references for local handover review (`95f4199`, `b0f6dba`).
- Added local release verification evidence and sprint artifacts for the 2026-04-28 packet (`b0f6dba`, `5fb4ec0`).
- Added C1-C8 commercial sprint artifacts and K-6 signing status (`5fb4ec0`).
- Documented remaining blockers: K-2/C4 latency under load, live UAT sessions, founder GPG signatures, sovereign-cluster validation, and commercial sign-off.
