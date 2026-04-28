# Changelog

## v1.0.0 Local Handover Packet - 2026-04-28

This changelog summarizes the release state represented by the latest local commits through `b0f6dba`. Cluster-gated validation remains open until the sovereign environment is available.

### Features

- Added modular FastAPI route slices for auth, data, graph, health, ingest, query, and admin flows (`7fe47b3`).
- Added SQL-only fast-path synthesis, query plan cache, and latency hot-path tests (`bccc061`).
- Added TRL-safe `trl_stages` database view and canonical schema alias coverage (`c1d82b8`, `4bf6bd6`, `964c2bb`).
- Added SSO endpoints, audit fixes, and production schema guardrails (`0dc388d`).
- Added phase 7 sovereign activation packet, Kubernetes/Helm readiness assets, C4 load-test assets, and data intake helpers (`7f3f5b2`, `75a59c6`).
- Added C1-C8 commercial sprint artifacts and K-6 signing status (`5fb4ec0`).
- Added Tier 1, Tier 2, and Tier 3 UAT query sets for live acceptance sessions.

### Security

- Added Qdrant zero-vector CRITICAL health behavior (`f2208f9`, `6100a25`, `52c7a67`).
- Added ADR-006 genesis hash pinning and `lineage_intact` audit-chain health field (`e727d54`).
- Added DPDP UI, consent flows, and audit binding improvements (`0dc388d`, `454f332`).
- Added live red-team replay evidence and rate-limit handling updates (`8ee6bfc`, `30dfb18`, `f76c28e`).
- Purged production-forbidden vocabulary from active paths and added full-repo vocabulary evidence (`cabc4be`, `0a3d602`, `c11bc15`, `b0f6dba`).
- Recorded final local code-review blockers in `BACKLOG.md` and `evidence/2026-04-28/code_review_final.md`.

### Performance

- Added K-4 cold-query latency evidence and publication-count cache warm path (`26f4e77`, `c38421a`).
- Added K-2 100-user load-test evidence and follow-up local baseline report (`14d23db`, `b0f6dba`).
- Added vector-drift scheduler evidence and quality-bar scorecard updates (`1f0be5f`, `40c986a`).
- Added local performance baseline evidence showing Docker/Colima and local service blockers for this workstation.

### Fixes

- Fixed ConsentBanner, ResearcherDashboard, LangGraph API tests, and PII injection handling (`454f332`).
- Fixed 15 code-review issues across security, performance, and duplicated logic (`622217b`).
- Fixed schema parity and RLS-related tests, including rate-limit handling in tier-isolation tests (`692c2ed`, `30dfb18`, `d28f276`, `62a127f`).
- Fixed health endpoint table counts, prompt sanitiser encoding, and query response evidence generation (`da6c967`, `92d3bb3`, `2743379`).
- Fixed API route split coverage and evidence traceability for K-1, K-3, K-4, and K-5A.

### Operations

- Pushed local release verification evidence to `main` (`b0f6dba`).
- Added handover manifest, final checklist, and evidence cross-references for local handover review.
- Added schema parity evidence: `tests/data/test_schema_parity.py` passed 16 tests.
- Coverage run remains inconclusive locally because the full suite ended abnormally after collection and live API-dependent tests; evidence is recorded.
- C4 remains pending for target-stack optimization and fresh load validation.
- Final `v1.0.0-eternal` signing remains blocked on founder GPG key and live cluster evidence.
