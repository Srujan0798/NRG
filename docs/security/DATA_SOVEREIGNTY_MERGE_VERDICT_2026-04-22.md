# Data Sovereignty Merge Verdict

Date: 2026-04-22  
Scope: `/Users/srujansai/Desktop/NRG DB/National_Research_Database/` to `nrg_research.db` and Qdrant collection `nrg_research`

## Final Answer

Safe to delete the Desktop source directory: **YES, with retained DB and Qdrant backups.**

Conditions:

1. Keep a backup of the repaired `nrg_research.db`.
2. Keep a Qdrant collection snapshot/export for `nrg_research` after the 2026-04-22 re-index.

Reason: all logical source rows are now present in SQLite and all 3,310 research documents are represented in Qdrant payloads, but the source `.txt` files are still the easiest rebuild source if both Qdrant and the source directory are deleted.

Qdrant snapshot created locally:

```text
nrg_research-7013972377210306-2026-04-22-08-01-38.snapshot
size=134,401,024 bytes
checksum=32f81b0ab90570ac49be24f6031643fa467d3da32c13b10bac0dd8461c7fb003
```

## Verification Command

```bash
.venv/bin/python scripts/verify_db_merge.py
```

Latest result:

```text
VERDICT: PASS
Warnings: 6
Errors: 0
```

The warnings are source-inherited issues, not merge loss:

- `projects.csv:27` has an unescaped comma in a project title and is repaired logically.
- `projects.csv:51` glues `PRJ_5050` and `PRJ-00001` onto one physical line.
- `labs_institutions.csv:41` glues `LAB_040` and `LAB-0001` onto one physical line.
- `funding_transactions.csv:99` glues `TXN_9098` and `TXN-000001` onto one physical line.
- 8 lab director IDs in the source are not present in `researchers`.
- 2 lab affiliation values in the source do not have matching normalized `institutions` rows.

## Table Counts

| Table | Source Logical Count | DB Count | Status |
|---|---:|---:|---|
| `researchers` | 5,615 | 5,615 | PASS |
| `publications` | 12,000 | 12,000 | PASS |
| `labs` | 890 | 890 | PASS |
| `projects` | 8,050 | 8,050 | PASS |
| `patents` | 3,000 | 3,000 | PASS |
| `collaborations` | 5,000 | 5,000 | PASS |
| `funding_records` | 15,436 | 15,436 | PASS |
| `research_documents` | 3,310 `.txt` files | 3,310 | PASS |
| `institutions` | Derived | 181 | PASS |

The earlier preliminary counts of `projects=8,049`, `labs=889`, and `funding_records=15,435` were physical CSV parser counts. They were understated because the source CSVs contain malformed physical lines that hide legitimate logical records.

## Missing And Repaired Rows

| Issue | Root Cause | Resolution |
|---|---|---|
| `PRJ_5026` absent from DB | Unescaped comma in title shifted columns, causing amount parse failure | Inserted the recovered record with title `High-pressure-temperature Behavior of (Mg, Fe)2GeO4: Analogues for Silicates of Deep Exoplanet Interiors` |
| `PRJ-00001` absent from DB | Glued to `PRJ_5050` on the same physical CSV line | Inserted from the same CSV line, cross-checked against `JSON_Data/projects.json` and `Graph/nodes.json` |
| `PRJ_5050.research_area` corrupted | Same glued line produced `Earth SciencesPRJ-00001` | Updated to `Earth Sciences` |
| `LAB-0001` absent from DB | Glued to `LAB_040` on the same physical CSV line | Inserted and normalized affiliation to the existing DRDO institution row |
| `LAB_040.director_researcher_id` corrupted | Same glued line produced `RES_1122LAB-0001` | Updated to `RES_1122` |
| `TXN-000001` absent from DB | Glued to `TXN_9098` on the same physical CSV line | Inserted from CSV/JSON cross-check |
| `TXN_9098.agency` corrupted | Same glued line produced `NMHSTXN-000001` | Updated to `NMHS` |
| 2,191 `research_documents.access_tier` rows differed from source file metadata | DB tier values had drifted from document frontmatter | Updated from `Research_Documents/*.txt` metadata |

## Research Documents

Result: **PASS**

- `Research_Documents/`: 3,310 `.txt` files.
- `research_documents`: 3,310 rows.
- Every `.txt` filename stem matches one DB `document_id`.
- DB document metadata now matches source frontmatter for title, researcher IDs, affiliation, publication year, keywords, research area tags, access tier, and category.

## Qdrant Provenance

Result: **PASS after re-index**

Before repair:

- Qdrant had 10,800 payloads.
- Those payloads covered only 1,800 distinct documents.
- Explanation: 1,800 documents x 6 chunks each = 10,800 points.
- The `research_documents_batch3.json` and `qdrant_ready_payload_batch3.json` files contain the same 1,800 document IDs as their non-batch3 counterparts, so they were not additive.

After repair:

- Qdrant has 19,322 payloads.
- Qdrant covers all 3,310 DB/source document IDs.
- Every Qdrant payload has `text`/`content`, `document_id`/`source_id`, and `source_type=research_document`.
- Chunk distribution: 610 documents with 5 chunks, 2,628 documents with 6 chunks, 72 documents with 7 chunks.
- Embedding model used for the repair: `sentence-transformers/all-MiniLM-L6-v2` with 384-dimensional vectors, matching the live collection size.

## JSON Data Verification

Result: **PASS**

`JSON_Data/` files are generation intermediates or subsets, not additional authoritative data:

| File | IDs | Status |
|---|---:|---|
| `researchers.json` | 2,500 | Subset of `researchers.csv` |
| `projects.json` | 3,500 | Subset of logical `projects.csv` |
| `labs_institutions.json` | 350 | Subset of logical `labs_institutions.csv` |
| `funding_transactions.json` | 7,338 | Subset of logical `funding_transactions.csv` |
| `research_documents.json` | 1,800 | Subset of `research_documents` |
| `research_documents_batch3.json` | 1,800 | Same IDs as `research_documents.json` |
| `qdrant_ready_payload.json` | 1,800 | Subset of `research_documents` |
| `qdrant_ready_payload_batch3.json` | 1,800 | Same IDs as `qdrant_ready_payload.json` |

## Source Directory Classification

| Path | Classification | Disposition |
|---|---|---|
| Root CSVs | ARTIFACT | Fully merged into SQLite using logical-row repair rules. |
| `Research_Documents/` | ARTIFACT after Qdrant snapshot | Text content is embedded in Qdrant payloads; keep only until a Qdrant snapshot/export is retained. |
| `JSON_Data/` | ARTIFACT | Subsets/intermediates; no additional data beyond DB and Qdrant after repair. |
| `JSON_Data/Minimax_Docs/` | ARTIFACT | Covered by `Research_Documents/`, DB metadata, and Qdrant payloads. |
| `Queries/` | REFERENCE | Already copied byte-identically to `tests/fixtures/queries/`. |
| `Graph/` | REFERENCE | Neo4j import artifacts are not used by runtime NRG; current graph planning lives in `docs/specs/NEO4J_KNOWLEDGE_GRAPH_SPEC.md`. |
| `Scripts/` | ARTIFACT | Data generation scripts; not needed after verified merge. |
| `databases/`, `dbms/`, `transactions/` | ARTIFACT | Neo4j/local store artifacts from generation phase. |
| `deploy/`, `api/` | ARTIFACT | Standalone generation/deployment scaffolding; not used by project runtime. |
| `Blueprint.txt`, `Deployment_Strategy.txt`, `Database_Schema.json`, worklogs | REFERENCE | Useful historical context only; not required for current DB/RAG operation. |

## Reference Files Preserved

The useful query references were already present in the project and are byte-identical to the source copies:

- `tests/fixtures/queries/agentic_flow_validation_queries.json`
- `tests/fixtures/queries/nrid_test_queries.json`
- `tests/fixtures/queries/test_results.json`
- `tests/fixtures/queries/tier1_researcher_queries.json`
- `tests/fixtures/queries/tier2_policymaker_queries.json`
- `tests/fixtures/queries/tier3_industry_queries.json`

No additional source files need to be copied before deleting the source directory, provided the SQLite DB backup and Qdrant snapshot/export are retained.

## Final Verdict

The source directory is no longer required as an active data source. It can be deleted after retaining a repaired SQLite backup and the Qdrant snapshot/export. Without the Qdrant snapshot/export, deletion is not recommended because the full document body corpus would depend on the live Qdrant volume alone.
