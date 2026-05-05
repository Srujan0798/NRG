# NRG Portable Corpus

`CORPUS/` is the portable AI handoff pack for NRG. It contains exact mirrors of canonical files plus a verification rule. No summaries. No interpretations. Only facts and pointers.

## Verify Before Use

```bash
.venv/bin/python scripts/verify_corpus_sync.py
```

Expected: `ok: true`

## What Is Here

**Exact mirrors** (byte-identical to canonical repo files):
- `Core_Idea_Clean.md` — product vision, UX contract, principles
- `db_struct.sql` — canonical PostgreSQL schema (58 tables)
- `killer_queries.yaml` — query benchmark and adversarial cases
- `api/endpoint_matrix.md` — every FastAPI endpoint, method, auth guard
- `quality/quality_bar.md` — 6 hard constraints (C1-C6)
- `state/current_state.md` — blockers, in-progress, shipped
- `state/source_of_truth_map.md` — canonical files vs mirrors
- `SQL_AUDIT_REPORT_DHAIRYA.md` — formatted Dhairya audit (17 queries)
- `SQL_AUDIT_RAW_dhairya.sql` — raw Dhairya audit SQL
- `SQL_AUDIT_REPORT_CLEAN.md` — short derived summary
- `schema/*` — 5 schema context files

**Meta files:**
- `CORPUS_INDEX.md` — master reading guide and reading order
- `README.md` — this file
- `VERIFY.md` — verification rule: scan actual source files, verify against requirements

## What Is NOT Here

No summaries. No interpretations. No condensed descriptions of:
- Architecture — read `src/`, `docs/architecture/` directly
- Frontend structure — read `frontend/src/` directly
- Deployment — read `docker-compose.yml`, `infrastructure/` directly
- Auth flow — read `src/api/routes/auth.py`, `src/auth/` directly
- Testing — read `tests/`, `pytest.ini` directly
- Tech stack — read `pyproject.toml`, `frontend/package.json` directly

## How an AI Should Use This

1. Read `CORPUS_INDEX.md` for reading order
2. Read exact mirrors for requirements and constraints
3. Read `VERIFY.md` for what actual source files to scan
4. Scan `src/`, `frontend/src/`, `tests/`, `docker-compose.yml`, `infrastructure/`, `.github/workflows/` directly
5. Verify: does source code match `Core_Idea_Clean.md` requirements?
6. Report: `PASS`, `FAIL`, `MISSING`, `BLOCKED`

## Canonical Files (for reference)

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

For any v1.0-building AI:
1. `CORPUS/` (this folder)
2. `.claude/CURRENT_STATE.md`
3. `prompts_hybrid/00_INDEX.md`
