# NRG Portable Corpus

`CORPUS/` is the portable AI handoff pack for NRG. An AI agent given only `CORPUS/` should understand the entire project: what it is, how it is built, how to run tests, how to deploy, and what is blocked.

## Verify Before Use

```bash
.venv/bin/python scripts/verify_corpus_sync.py
```

Expected: `ok: true`

## Reading Order for AI Agents

1. **Start here:** `CORPUS_INDEX.md` — master reading guide
2. Follow the 8-step order defined in `CORPUS_INDEX.md`

## File Inventory

### Product & Data
- `Core_Idea_Clean.md` — product vision, UX contract, principles
- `db_struct.sql` — canonical PostgreSQL schema (58 tables)
- `killer_queries.yaml` — 3 launch queries + 10 adversarial breakers

### Schema Context
- `schema/schema_hints.md` — text-to-SQL hints
- `schema/schema_value_synonyms.md` — value synonym rules
- `schema/business_term_glossary.yaml` — business-term-to-schema mapping
- `schema/nrg_full_schema.sql` — full schema reference
- `schema/production_schema.sql` — production schema reference
- `schema/sqlite_schema.sql` — development SQLite schema

### Audit & Benchmarks
- `SQL_AUDIT_REPORT_DHAIRYA.md` — formatted Dhairya audit (17 queries, 41% baseline)
- `SQL_AUDIT_RAW_dhairya.sql` — raw Dhairya audit SQL
- `SQL_AUDIT_REPORT_CLEAN.md` — short derived summary

### Architecture
- `architecture/system_overview.md` — backend, frontend, infra fit
- `architecture/data_pipeline.md` — ingest → store → query → answer
- `architecture/security_model.md` — auth, DPDP, PII, audit chain

### API
- `api/endpoint_matrix.md` — every FastAPI endpoint, method, auth guard
- `api/auth_flow.md` — JWT, tiers, login/logout/refresh

### Frontend
- `frontend/structure.md` — pages, components, routing, key files
- `frontend/design_system.md` — design tokens, component library

### Quality & Testing
- `quality/quality_bar.md` — 6 hard constraints (C1-C6)
- `quality/testing_strategy.md` — test structure, commands, CI

### State
- `state/current_state.md` — blockers, in-progress, shipped
- `state/source_of_truth_map.md` — canonical files vs mirrors

### Operations
- `tech_stack.md` — what tech is used where, versions
- `deployment/docker_compose.md` — services, ports, env vars
- `deployment/infrastructure.md` — K8s, nginx, kong, grafana, prometheus

## Canonical Files (read if you need depth)

`CORPUS/` is a mirror. Canonical files live in their normal repo locations:

| Canonical source | Corpus mirror |
|-----------------|---------------|
| `Core_Idea_Clean.md` | `CORPUS/Core_Idea_Clean.md` |
| `db_struct.sql` | `CORPUS/db_struct.sql` |
| `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md` | `CORPUS/SQL_AUDIT_REPORT_DHAIRYA.md` |
| `docs/reports/SQL_AUDIT_RAW_dhairya.sql` | `CORPUS/SQL_AUDIT_RAW_dhairya.sql` |
| `tests/benchmarks/killer_queries.yaml` | `CORPUS/killer_queries.yaml` |
| `docs/specs/API_ENDPOINT_MATRIX.md` | `CORPUS/api/endpoint_matrix.md` |
| `.claude/quality-bar.md` | `CORPUS/quality/quality_bar.md` |
| `.claude/CURRENT_STATE.md` | `CORPUS/state/current_state.md` |
| `docs/specs/NRG_SOURCE_OF_TRUTH_MAP_2026-04-30.md` | `CORPUS/state/source_of_truth_map.md` |
| `src/data/schema/*` | `CORPUS/schema/*` |

## v1.0 Handoff Pack

For any v1.0-building AI, provide:
1. `CORPUS/` (this folder)
2. `.claude/CURRENT_STATE.md`
3. `prompts_hybrid/00_INDEX.md`
4. `docs/specs/NRG_SOURCE_OF_TRUTH_MAP_2026-04-30.md`

## Size

~25 files. Estimated reading time: 60-90 minutes for full comprehension.
