# NRG Schema Reference

## Canonical Source

The authoritative production schema is:

```text
db_struct.sql
```

That root file is the official PostgreSQL dump and must be read before any work
touching Text-to-SQL, RAG retrieval, schema mapping, data validation, or query
benchmarks.

## Active Schema Support Files

The active schema guidance used by the Text-to-SQL path lives in
`src/data/schema/`:

| File | Purpose |
| --- | --- |
| `schema_hints.md` | Table, column, join, and Dhairya failure-pattern hints |
| `schema_value_synonyms.md` | Value synonyms such as `TRL 9` -> `Level 9` |
| `business_term_glossary.yaml` | Business terms mapped to schema paths |
| `nrg_full_schema.sql` | SQLite/local dev schema reference |
| `production_schema.sql` | Production DDL reference |
| `sqlite_schema.sql` | Older SQLite schema reference |

## Portable Corpus Mirror

`CORPUS/` mirrors the key schema and benchmark files for AI handoff. It is not
the canonical source tree. Verify mirrors before using them:

```bash
python3 scripts/verify_corpus_sync.py
```

## Dhairya SQL Audit

For SQL quality, the official audit files are:

- `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md`
- `docs/reports/SQL_AUDIT_RAW_dhairya.sql`

The corpus file `CORPUS/SQL_AUDIT_REPORT_CLEAN.md` is a derived short summary.
It is useful for quick orientation, but it must not replace the official report.

## Design Decisions

- Production database: PostgreSQL 14 on Neon serverless
- Development database: SQLite subset where explicitly configured
- Access control: tier-aware filtering across query and UI paths
- Query benchmark: Dhairya audit + `tests/benchmarks/killer_queries.yaml`
