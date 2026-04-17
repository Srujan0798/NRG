# Agent-3 Data Report

## Summary
- Repaired `scripts/seed_database.py` schema mismatches for `funding_records`.
- Successfully seeded the SQLite database with high-quality institutional data.
- Rebuilt Qdrant vector index with 1,500 synthetic points for robust RAG performance.

## Database Statistics
- researchers: 200
- institutions: 24
- publications: 500
- labs: 50
- funding_records: 100

## Vector Index
- Collection: `nrg_research`
- Points: 1515 (1500 synthetic + 15 test)
- Model: `ai4bharat/IndicBERTv2-SS` (768-dim)

## Retrieval Quality
- Verified via `NRGWorkflow` run:
  - Query: "Find robotics researchers in Gujarat"
  - Result: Correctly identified researchers and returned synthesized response from data.
