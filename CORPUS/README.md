# NRG Portable Corpus

`CORPUS/` is useful and should stay. It is the portable AI handoff pack for
NRG: a compact mirror of the files an agent needs to understand the product,
schema, Dhairya SQL audit patterns, and benchmark questions quickly.

It is **not** the live source tree. Canonical files remain in their normal repo
locations. Before giving `CORPUS/` to any AI agent, verify that the mirrors are
in sync:

```bash
.venv/bin/python scripts/verify_corpus_sync.py
```

Expected successful run:

```text
CORPUS sync: PASS
```

If the virtualenv is not available yet, `python3 scripts/verify_corpus_sync.py`
is acceptable only after dependency setup is complete and the command resolves
to the project Python version.

Latest Batch 4 verification: `PASS` on 2026-05-02. Evidence:
`evidence/2026-05-02/batch4_data_sql_schema/D4-10_corpus_sync.json`.

Latest current-tree recheck: `PASS` on 2026-05-05 with `ok: true`. Evidence:
`evidence/2026-05-05/80_task_dispatch_recheck/README.md`.

## Canonical Files And Mirrors

| Canonical source | Corpus mirror | Purpose |
| --- | --- | --- |
| `Core_Idea_Clean.md` | `CORPUS/Core_Idea_Clean.md` | Product vision, UX contract, user-visible answer-engine behavior |
| `db_struct.sql` | `CORPUS/db_struct.sql` | Official PostgreSQL schema dump |
| `docs/reports/SQL_AUDIT_RAW_dhairya.sql` | `CORPUS/SQL_AUDIT_RAW_dhairya.sql` | Raw external Dhairya audit log |
| `tests/benchmarks/killer_queries.yaml` | `CORPUS/killer_queries.yaml` | Query benchmark and adversarial SQL/RAG cases |
| `src/data/schema/schema_hints.md` | `CORPUS/schema/schema_hints.md` | Text-to-SQL table/column hints |
| `src/data/schema/schema_value_synonyms.md` | `CORPUS/schema/schema_value_synonyms.md` | Value synonym rules |
| `src/data/schema/business_term_glossary.yaml` | `CORPUS/schema/business_term_glossary.yaml` | Business-term-to-schema mapping |
| `src/data/schema/*.sql` | `CORPUS/schema/*.sql` | Development and production schema references |

## Dhairya Audit Rule

The official formatted Dhairya audit is:

```text
docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md
```

The raw audit is:

```text
docs/reports/SQL_AUDIT_RAW_dhairya.sql
```

`CORPUS/SQL_AUDIT_REPORT_CLEAN.md` is only a short derived summary for fast
handoff. It must not replace the official formatted report or the raw audit.

## v1.0 Handoff Pack

For any v1.0-building AI, provide this minimum pack:

1. `Core_Idea_Clean.md`
2. `docs/specs/NRG_SOURCE_OF_TRUTH_MAP_2026-04-30.md`
3. `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md`
4. `db_struct.sql`
5. `CORPUS/`
6. `.claude/CURRENT_STATE.md`
7. `prompts_hybrid/00_INDEX.md`
8. `prompts_hybrid/02_main_flow_stone.md`
9. `prompts_hybrid/03_frontend_zero_flaw_stone.md`
10. latest relevant `evidence/2026-04-30/`

The corpus is valuable because it prevents agents from missing schema and audit
context. It becomes dangerous only if an agent treats it as the only truth or
ignores the canonical files above.
