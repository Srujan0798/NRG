# Local Full-Health Closure Report

Generated: 2026-05-01

## Scope

This pass closed local health and vector-retrieval blockers that remained after the GLM visible-query gates. It does not certify deployed production, sovereign-cluster load, founder signing, or complete official data coverage.

## Changes Made

- Treated small Qdrant collections below `indexing_threshold` as healthy exact-scan collections instead of false-red index failures.
- Fixed vector drift scoring so normal checks compare against the persisted known-good baseline instead of overwriting it or using static placeholder expectations.
- Added `scripts/repair_qdrant_payloads.py` to repair stale Qdrant points with zero vectors or missing retrieval metadata while keeping strict RBAC filters.
- Repaired the local `nrg_research` Qdrant collection:
  - Before: 1,800 points, 1,800 zero vectors, 1,800 missing `access_tier`.
  - After: 1,800 non-zero vectors, 1,800 points with `access_tier`, 1,763 points with source/topic/institution metadata.
- Established a fresh local vector baseline and proved drift GREEN.

## Evidence

| Check | Result | Evidence |
|---|---:|---|
| Qdrant stale-payload audit before repair | FAIL confirmed | `qdrant_payload_access_tier_audit.log`, `qdrant_vector_norm_probe.log` |
| Qdrant repair dry run | 1,800 repairable points | `qdrant_repair_dry_run.log` |
| Qdrant repair apply | 1,376 remaining points repaired after an interrupted long-text pass | `qdrant_repair_apply_short_text.log` |
| Qdrant metadata audit after repair | PASS local collection repaired | `qdrant_payload_access_tier_audit_after_repair.log` |
| RAG retrieval sample after repair | PASS tier-filtered rows returned | `qdrant_retrieval_sample_after_repair.log` |
| Vector baseline establishment | PASS | `vector_drift_establish_baseline_after_qdrant_repair.log` |
| Vector drift score | GREEN, 1.000 | `vector_drift_full_score_after_baseline_fix.log` |
| Health endpoints | PASS local stack | `local_stack_health_after_qdrant_repair.json` |
| Health/observability tests | 58 passed | `health_observability_regression_after_qdrant_repair.log` |
| Audit chain | PASS | `audit_chain_verify_after_qdrant_repair.log` |
| Corpus sync | PASS | `corpus_sync_after_qdrant_repair.log` |
| External final gates | BLOCKED | `final_external_gates_after_qdrant_repair.log` |

## Remaining Blockers

- Data quality is still degraded: `data_quality_scorecard_postgres.log` shows schema coverage, PII scan, and consistency passed, but overall data quality remains FAIL because 12 official core tables are empty and several optional columns have 100% null rates.
- External production gates remain blocked without deployed frontend/API URLs, production Qdrant target, explicit cluster-load context, and founder private signing key.
- Local Qdrant has 1,800 repaired points. Production-level Qdrant still needs the real production corpus baseline in the target environment.

## Status

Local health and vector retrieval are materially improved and freshly evidenced. The project is not 100% complete until the data-completion and external production gates above are closed.
