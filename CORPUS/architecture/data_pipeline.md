# NRG Data Pipeline

## Overview

```text
Ingest → Store → Index → Query → Plan → Retrieve → Synthesize → Answer
```

## 1. Ingestion

**Path:** `src/api/routes/ingest.py`, `src/data/`

- Documents submitted via `/api/ingest` (Tier 1 only)
- Background job processes document
- Extracts text, metadata, citations
- Stores raw document + extracted fields

## 2. Storage

**Primary:** PostgreSQL 16 (`db_struct.sql` — 58 tables)

| Data Type | Tables | Examples |
|-----------|--------|----------|
| Researchers | `researchers`, `researcher_labs`, `researcher_publications` | Profile, affiliations, publications |
| Publications | `publications`, `publication_keywords` | Title, abstract, journal, keywords |
| Funding | `funding`, `funding_records`, `innovation_grant_from_govt` | Grants, amounts, years |
| Patents | `patents`, `combined_ipo_patent_data` | Filings, titles, inventors |
| Labs | `labs`, `institutions` | Lab name, institution, location |
| Courses | `academic_courses_details` | Credits, financial year, institute |
| TRL | `innovations_at_various_stages_of_technology_readiness_level` | Innovation stage, year |

**Vector Store:** Qdrant (`nrg_research` collection)
- Embeddings for semantic search
- Dimension from active embedder (not hardcoded)
- Falls back gracefully if unavailable

## 3. Query Flow

**Path:** `src/orchestration/`, `src/skills/`

1. **User asks** → `/query` or `/api/query/stream`
2. **Planner** (`src/orchestration/nodes/planner.py`) decomposes into sub-queries
   - Single-hop: direct SQL or RAG
   - Multi-hop: DAG of dependent sub-queries
3. **SQL Skill** (`src/skills/text_to_sql/`) generates PostgreSQL query
   - Uses schema hints, synonyms, business glossary
   - Dhairya failure patterns guard against common errors
4. **RAG Skill** (`src/skills/rag/`) retrieves relevant documents from Qdrant
5. **Synthesizer** combines SQL results + RAG evidence
   - Cloud-gated first (if enabled)
   - Local SLM second
   - Rule-based fallback always available
6. **Response** includes: answer, citations, SQL, audit ID, confidence

## 4. Audit Trail

**Path:** `src/audit/`

Every query creates an audit event:
- `user_id`, `persona`, `jwt_jti`, `request_fingerprint`
- HMAC-signed with per-user derived key
- Appended to `.audit/chain.jsonl`
- Genesis hash pinned in `.audit/genesis_hash.pin`
- Verification via `/audit/verify`

## 5. Quality Checks

**Path:** `src/observability/`, `scripts/`

- **Data Quality:** `scripts/quality_bar_scorecard.py` — scorecard PASS/FAIL
- **Vector Drift:** `scripts/vector_drift_check.py` — cosine shift > 0.05 triggers retrain
- **PII Scan:** `src/security/pii/` — blocks Indian PII (PAN, Aadhaar, mobile, etc.)
- **Egress Guard:** `src/security/egress_guard/` — only allowlisted schema fragments to LLM
