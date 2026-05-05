# POINTER: Data Pipeline

> **Do not trust this file as the source of truth.** Read the actual files listed below and verify against `Core_Idea_Clean.md` requirements.

## Where to Read

| Stage | Actual Source Files | What to Verify |
|-------|--------------------|----------------|
| **Ingestion** | `src/api/routes/ingest.py`, `src/data/` | Document intake, background jobs |
| **Storage** | `db_struct.sql`, `src/config/database.py` | 58 tables, PostgreSQL, migrations |
| **Vector Store** | `src/skills/rag/`, `scripts/build_qdrant_index.py` | Qdrant collection, embeddings |
| **Query Planning** | `src/orchestration/nodes/planner.py` | Multi-hop DAG, sub-query decomposition |
| **SQL Generation** | `src/skills/text_to_sql/` | Schema hints, synonyms, Dhairya guards |
| **RAG Retrieval** | `src/skills/rag/` | Vector search, evidence retrieval |
| **Synthesis** | `src/orchestration/nodes/synthesizer.py` or equivalent | Cloud/local/rule-based cascade |
| **Response** | `src/api/routes/query.py` | Answer format, citations, audit ID |
| **Audit** | `src/audit/`, `.audit/chain.jsonl` | Every query logged, HMAC signed |

## Verification Commands

```bash
# Check ingestion route
grep -n "ingest" src/api/routes/ingest.py | head -5

# Check schema tables
grep -c "CREATE TABLE" db_struct.sql

# Check Qdrant integration
grep -rn "qdrant" src/skills/rag/ | head -10

# Check planner
ls src/orchestration/nodes/planner.py

# Check text-to-sql
ls src/skills/text_to_sql/

# Check query route
grep -n "def query" src/api/routes/query.py | head -5

# Check audit
ls src/audit/ .audit/chain.jsonl .audit/genesis_hash.pin
```

## Requirements to Verify Against

From `Core_Idea_Clean.md`:
- Ask → Plan → Retrieve → Synthesize → Verify → Prove loop
- SQL for exact data, RAG for documents, graph for relationships
- Answer must include: citations, SQL, audit ID, confidence, freshness

**Read the actual source files. Do not trust this pointer.**
