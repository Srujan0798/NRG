# NRG Database Schema

## ⚠️ Canonical Source: See `CORPUS/`

**The authoritative schema reference is in `CORPUS/`:**
- `CORPUS/db_struct.sql` — Production PostgreSQL dump (58 tables, **THE SOURCE OF TRUTH**)
- `CORPUS/schema/` — All schema files: nrg_full_schema.sql, production_schema.sql, sqlite_schema.sql
- `CORPUS/schema_hints.md` — AI SQL hints (used by text-to-SQL engine)
- `CORPUS/schema_value_synonyms.md` — Value synonyms (used by text-to-SQL engine)
- `CORPUS/business_term_glossary.yaml` — Business term glossary (used by schema retriever)

## Local Schema Files

| File | Description |
|------|-------------|
| `schema_hints.md` | **IN USE** — AI hints for text-to-SQL generation |
| `schema_value_synonyms.md` | **IN USE** — Synonym mappings for SQL generator |
| `business_term_glossary.yaml` | **IN USE** — Business glossary for schema retriever |
| `nrg_full_schema.sql` | SQLite dev schema (18 tables) |
| `production_schema.sql` | PostgreSQL ideal schema |
| `sqlite_schema.sql` | Older SQLite schema |

## Migrations

`migrations/` — SQL migration scripts (Alembic format)

## Deprecated

`researcher_db.sql` — removed, use `CORPUS/db_struct.sql`
`OFFICIAL_POSTGRESQL_SCHEMA.md` — removed, use `CORPUS/db_struct.sql`

## Design Decisions

- **Production:** PostgreSQL 14 on Neon serverless
- **Development:** SQLite (18 tables, subset)
- **Access Control:** Row-level security by tier (1=Researcher, 2=Government, 3=Industry)
- **AI SQL Quality:** See `CORPUS/SQL_AUDIT_REPORT_CLEAN.md`
