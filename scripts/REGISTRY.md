# NRG Script Registry

Date: 2026-05-01

This registry records which scripts are active, which are compatibility
wrappers, which were retired, and which still need deeper review before any
move or deletion.

## Rules

- Do not delete a script until reference search proves no active caller and no
  unique operational behavior.
- Prefer a maintained Python entry point for cross-platform operational logic.
- Keep shell scripts when they are container glue, local compose helpers, or
  simple wrappers.
- Any script that writes proof must write under `evidence/YYYY-MM-DD/` or accept
  an explicit output path.
- Any script that handles secrets must avoid printing secret values.

## Active Canonical Entry Points

| Area | Canonical scripts | Notes |
| --- | --- | --- |
| Bootstrap and local services | `bootstrap.sh`, `setup_llm.sh`, `start_local_llm.py` | Local setup and model runtime helpers |
| Health and gates | `health_check.py`, `deployment_gate.py`, `run_final_external_gates.py`, `run_test_suite.sh`, `run_ui_ux_check.sh` | Current gate and validation runners |
| Source-truth checks | `verify_corpus_sync.py`, `forbidden_vocab_check.sh`, `check_workflow_links.sh`, `validate_contracts.py` | Required before external handoff claims |
| Schema and database | `schema_sync.py`, `check_schema_sync.py`, `init_db.py`, `data_integrity_check.sql` | Keep both schema CLIs until `check_schema_sync.py` is folded into `schema_sync.py` |
| Audit and security | `audit_chain_health_check.py`, `audit_investigate.py`, `audit_rebuild.py`, `red_team_live_replay.py`, `red_team_replay.sh` | Audit repair, proof, and red-team replay |
| Sealing and compliance | `chain_seal_attestation.py`, `eternal_seal_execute.py`, `phase7_preflight.py`, `pre_tag_checklist.py` | Cluster and release-gated workflows |
| Data quality | `data_quality_scorecard.py`, `quality_bar_scorecard.py`, `vector_drift_check.py`, `vector_drift_scheduler.py` | Scorecards, drift checks, and quality gates |
| Seeding | `seed_release_data.py`, `seed_production_initial_dataset.py`, `seed_production_tables.py`, `seed_acceptance_data.py`, `seed_acceptance_users.py`, `seed_local_quality_fixtures.py` | Keep until a dedicated seed package replaces them |
| Ingestion and vectors | `ingest_qdrant.py`, `ingest_documents.py`, `ingest_nrg_db.py`, `build_qdrant_index.py`, `repair_qdrant_payloads.py`, `init_qdrant.py` | Current RAG/vector data path |
| Migration | `migrate_data_to_postgresql.py`, `migrate_sqlite_to_pg.py`, `verify_db_merge.py`, `verify_intake_bundle.py` | Keep pending migration package consolidation |
| Deployment and backup | `deploy.py`, `deploy.sh`, `deployment_gate.py`, `runtime_image_scan_gate.py`, `backup_nrg.sh`, `backup_db.sh` | `runtime_image_scan_gate.py` validates captured runtime-image scan artifacts; `deploy.sh` and `backup_db.sh` are compatibility wrappers |
| Performance and cost | `load_test.py`, `load_test_100users.py`, `run_load_test.py`, `slo_report.py`, `llm_cost_report.py` | Keep until C4/performance gates are consolidated |
| Acceptance and evidence | `run_acceptance_verification.py`, `run_critical_path.sh`, `run_critical_path_final.sh`, `capture_killer_query_evidence.py`, `uat_run_session.py`, `build_before_after_gallery.mjs` | Current acceptance and evidence helpers |
| JWT and security utilities | `generate_jwt_keys.sh`, `issue_test_jwt.py`, `rotate_jwt_secret.py`, `check_jwt_secret_config.py` | Keep; secret values must never be printed |

## Structured Script Packages

| Package | Status | Notes |
| --- | --- | --- |
| `scripts/audit/` | Active | Browser and UI audit helpers |
| `scripts/compliance/` | Active | Compliance document compilation and assessment |
| `scripts/ingestion/` | Active | Batch embedding and vector ingestion internals |
| `scripts/migration/` | Active | PostgreSQL migration internals |
| `scripts/security/` | Active | Security perimeter hardening helper |
| `scripts/strategy/` | Active | Strategy document validation/compilation |

## Compatibility Wrappers

| Script | Canonical target | Reason kept |
| --- | --- | --- |
| `backup_db.sh` | `backup_nrg.sh` | Older runbooks and cron entries may still call the old name |
| `deploy.sh` | Local Docker Compose helper; cloud release uses `deploy.py` and `deployment_gate.py` | Keeps a simple local stack command without pretending to be the full release path |

## Retired In This Cleanup

| Removed script | Reason |
| --- | --- |
| `setup_dev.sh` | Obsolete local setup path that created `venv`; `bootstrap.sh` owns `.venv` setup |
| `smoke.sh` | Unreferenced shell smoke path; `health_check.py`, API tests, and deployment gates cover active checks |
| `verify_evidence.py` | Hardcoded to old `evidence/2026-04-25` files and unreferenced |
| `ingest_research_papers.py` | Superseded by `ingest_qdrant.py` and `scripts/ingestion/` package |
| `ingest_synthetic.py` | Old data generator not used by the current source-truth or release data path |

## Review Before Moving Or Deleting

| Candidate | Reason for review |
| --- | --- |
| `build_embeddings.py` | Overlaps vector ingestion, but may contain publication-specific behavior |
| `expand_database.py` | Old SQLite expansion helper; confirm no acceptance path still depends on it |
| `founder_laptop_seed.py` | User-specific local seed helper; preserve until replacement path is explicit |
| `seed_production_data.py` | Older production seed name; docs still reference newer replacement work |
| `prewarm_acceptance_cache.py` and `prewarm_release_cache.py` | Similar purpose, but both have historical references |
| `migrate_sqlite_to_pg.py` and `migrate_data_to_postgresql.py` | Similar migration area, but different modes and references |
| `load_test.py`, `load_test_100users.py`, and `run_load_test.py` | Consolidate after C4 load gate is finalized |
| `quality_bar_scorecard.py` and `data_quality_scorecard.py` | Different scorecard scopes; keep until reporting surfaces are unified |

## Next Consolidation Pass

1. Add tests for compatibility wrappers where needed.
2. Fold `check_schema_sync.py` behavior into `schema_sync.py` if any flags are
   still unique.
3. Collapse seed scripts into a `scripts/seed/` package with a single CLI.
4. Collapse load scripts into a `scripts/load/` package with one entry point.
5. Move root scripts by category only after all docs/tests/callers are updated.
