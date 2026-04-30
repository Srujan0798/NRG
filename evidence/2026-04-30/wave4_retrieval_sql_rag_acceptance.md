# Wave 4 Retrieval, SQL, and RAG Acceptance Evidence

Date: 2026-04-30

Scope: Canonical schema path, Text-to-SQL regressions, deterministic retrieval coverage, and explicit RAG/Qdrant health.

## What changed

- `src/data/database.py` now initializes SQLite from `src/data/schema/nrg_full_schema.sql`, the retained canonical schema file.
- `/health` now includes an explicit `rag` block derived from Qdrant and retriever health:
  - `status`
  - `retrieval_enabled`
  - `collection`
  - `vectors`
  - `qdrant_status`
  - `retriever_status`
  - `warning`
- Deterministic safe SQL now supports institution lookup through the catalog-backed builder.
- Safe SQL regression coverage now includes:
  - funding ranking
  - researcher ranking
  - institution lookup
  - publication ranking
  - PII block
  - document-only unsupported path

## Canonical Data Decision

The cleanup removed `src/data/schema/optimized_schema.sql`. That file was a duplicate of `src/data/schema/nrg_full_schema.sql`. Instead of restoring the duplicate, the legacy SQLite helper now uses `nrg_full_schema.sql`, matching `scripts/ingest_nrg_db.py`.

Current schema roles:

| File | Role |
| --- | --- |
| `db_struct.sql` | PostgreSQL/source-of-truth dump used by schema-aware Text-to-SQL prompt guidance. |
| `src/data/schema/nrg_full_schema.sql` | Canonical SQLite local/test ingestion schema. |
| `src/data/schema/production_schema.sql` | Historical production schema reference; not used by the fixed SQLite initializer. |

## RAG Health Semantics

`/health.qdrant` remains the raw vector-store signal. The new `/health.rag` summary makes product readiness explicit:

| Qdrant status | RAG status | Retrieval enabled | Meaning |
| --- | --- | --- | --- |
| `healthy` | `ready` | `true` | RAG can serve retrieval evidence. |
| `CRITICAL` | `critical` | `false` | Collection is empty; ingestion required. |
| `unavailable` | `degraded` | `false` | Qdrant cannot be reached; RAG must not masquerade as working. |

Live Qdrant population was not asserted in this local pass; the health endpoint now exposes the state honestly.

## Verification Commands

Schema red phase:

```bash
.venv/bin/python -m pytest tests/unit/test_database.py tests/unit/test_database_path.py tests/scripts/test_ingest_nrg_db.py tests/data/test_database_v2_schema_drift.py -q
```

Result before fix: 7 errors from missing `src/data/schema/optimized_schema.sql`.

Schema green phase:

```bash
.venv/bin/python -m pytest tests/unit/test_database.py tests/unit/test_database_path.py tests/scripts/test_ingest_nrg_db.py tests/data/test_database_v2_schema_drift.py -q
```

Result: 15 passed.

SQL regression red phase:

```bash
.venv/bin/python -m pytest tests/skills/test_safe_sql_builder.py::test_builds_institution_lookup_from_catalog tests/skills/test_safe_sql_builder.py::test_builds_publication_ranking_from_catalog -q
```

Result before fix: institution lookup failed as `unsupported`; publication ranking already passed.

SQL regression green phase:

```bash
.venv/bin/python -m pytest tests/skills/test_safe_sql_builder.py::test_builds_institution_lookup_from_catalog tests/skills/test_safe_sql_builder.py::test_builds_publication_ranking_from_catalog -q
```

Result: 2 passed.

Focused Text-to-SQL suite:

```bash
.venv/bin/python -m pytest tests/skills/test_safe_sql_builder.py tests/skills/test_text_to_sql_semantic_anomaly.py tests/skills/test_text_to_sql.py tests/skills/test_text_to_sql_rewriter.py tests/skills/test_schema_retriever.py tests/skills/test_schema_extractor.py -q
```

Result: 62 passed.

RAG and health suite:

```bash
.venv/bin/python -m pytest tests/api/test_health_endpoints.py tests/skills/test_rag.py tests/skills/test_rag_failures.py tests/skills/test_rag_embedder_retriever.py tests/skills/test_rag_ingest_reranker.py -q
```

Result: 57 passed.

Compile check:

```bash
.venv/bin/python -m py_compile src/data/database.py src/observability/health_checks.py src/api/main.py src/api/routes/health.py src/skills/text_to_sql/safe_sql_builder.py tests/api/test_health_endpoints.py tests/skills/test_safe_sql_builder.py
```

Result: exit 0.

## Remaining Scope

- Live PostgreSQL schema parity and `EXPLAIN ANALYZE` are still cluster/database dependent.
- Live Qdrant vector population is exposed by health but not proven locally in this pass.
- Full Dhairya 17-query live execution remains a later SQL acceptance task; this pass strengthens deterministic regressions and schema-aware guards.
