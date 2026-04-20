# Agent 3: Data + RAG Readiness

## Objective
Bring data and retrieval to production baseline.

## Must Fix
- seed process leaves publications/labs/funding_records at zero
- vector corpus too small

## Scope
- scripts/seed_database.py
- scripts/ingestion/qdrant_loader.py
- src/skills/rag/*
- dependency pinning for qdrant-client/server compatibility

## Done Criteria
1. SQLite non-zero counts: researchers, institutions, publications, labs, funding_records
2. Qdrant points_count >= 1000
3. RAG retrieval returns relevant chunks for IIT research queries
4. tests/skills/test_rag.py passes

## Current Status
- publications/labs/funding_records all 0
- Qdrant has only 15 points (too small for production RAG)

## Action Required
1. Run seed script to populate database:
   - Ensure scripts/seed_database.py runs successfully
   - Check for any import errors or missing data files
2. Re-index Qdrant:
   - Run scripts/ingestion/qdrant_loader.py
   - Increase documents indexed to at least 1000
3. Verify retrieval:
   - Test RAG queries return relevant chunks
4. Check dependencies:
   - Ensure qdrant-client version matches server version

## Key Files to Modify
- scripts/seed_database.py - Fix any issues preventing data load
- scripts/ingestion/qdrant_loader.py - Ensure all documents are indexed
- src/skills/rag/ - Ensure retrieval returns quality results