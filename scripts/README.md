# NRG Scripts Map

This directory contains operational scripts. Treat it as a maintained toolbelt,
not a dumping ground for one-off experiments.

## Current Script Categories

For per-script status, ownership, and cleanup decisions, see
[`REGISTRY.md`](REGISTRY.md).

| Category | Purpose | Examples |
| --- | --- | --- |
| Bootstrap and setup | Bring up local development or model dependencies | `bootstrap.sh`, `setup_llm.sh` |
| Health and verification | Validate API, schema, contracts, corpus, claims, and evidence | `health_check.py`, `deployment_gate.py`, `verify_corpus_sync.py`, `validate_contracts.py` |
| Seeding and data fixtures | Seed local, acceptance, release, and production-like datasets | `seed_release_data.py`, `seed_local_quality_fixtures.py`, `seed_production_tables.py` |
| Ingestion and vector index | Load documents, DB rows, embeddings, and Qdrant payloads | `ingest_qdrant.py`, `ingest_documents.py`, `build_qdrant_index.py` |
| Audit and security | Investigate, rebuild, seal, replay, or check audit/security paths | `audit_investigate.py`, `audit_rebuild.py`, `red_team_live_replay.py` |
| Performance and load | Run load tests, cold-query profiles, SLO reports | `load_test.py`, `slo_report.py` |
| Deployment and operations | Deploy, backup, preflight, image scan gates, and external-gate verification | `deploy.py`, `deployment_gate.py`, `runtime_image_scan_gate.py`, `backup_nrg.sh`, `run_final_external_gates.py` |
| Subpackages | Larger script families that already have internal structure | `ingestion/`, `migration/`, `audit/`, `security/`, `strategy/`, `compliance/` |

## Cleanup Rules

1. Before deleting a script, run a reference search across `README.md`, `docs/`,
   `tests/`, `.github/`, `.claude/`, `.agents/`, and `prompts_hybrid/`.
2. If two scripts overlap, keep the one with broader tests or current docs and
   migrate unique flags or checks before deletion.
3. Prefer Python for cross-platform operational logic. Keep shell scripts for
   container/bootstrap glue where shell is simpler.
4. Every new script must include a module docstring or top comment explaining:
   purpose, required environment variables, expected outputs, and failure mode.
5. Every script that writes evidence should write under `evidence/YYYY-MM-DD/`
   or accept an explicit output path.

## Consolidation Target

Future cleanup should move root-level scripts into clear subdirectories:

```text
scripts/
  audit/
  deploy/
  ingest/
  load/
  maintenance/
  seed/
  verify/
```

Do this in small commits with reference updates and tests. Do not move scripts
that are currently called by CI, Docker, or handover docs without updating those
call sites in the same commit.
