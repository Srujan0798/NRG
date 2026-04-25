# TP-B5 — FULL PATH: Re-Ingest Vectors into Qdrant

**Owner:** BACKEND / ML  
**Estimated Duration:** 30–60 minutes  
**Blockers:** TP-B3 (Qdrant must be running)  
**Priority:** P1 — Restores full RAG functionality

---

## Objective

Re-populate Qdrant with research paper embeddings. Restore vectors so RAG retrieval works again.

---

## Phase 1 — Check What Data Is Available

```bash
cd /Users/srujansai/Desktop/NRG

# Check for source documents
ls data/training/ 2>/dev/null | head -20
find data -name "*.pdf" -o -name "*.txt" -o -name "*.md" 2>/dev/null | head -20

# Check ingestion scripts
ls scripts/ingestion/
ls scripts/ingest*.py
```

---

## Phase 2 — Run Ingestion

### Option A: Quick Synthetic Data (Fastest)

```bash
cd /Users/srujansai/Desktop/NRG
.venv/bin/python scripts/ingest_synthetic.py --count 1000
```

### Option B: Real Documents

```bash
cd /Users/srujansai/Desktop/NRG
.venv/bin/python scripts/ingest_documents.py --source-dir data/training/
```

### Option C: Database-to-Qdrant

```bash
cd /Users/srujansai/Desktop/NRG
.venv/bin/python scripts/ingestion/db_to_qdrant.py
```

---

## Phase 3 — Verify Ingestion

```bash
curl -s http://localhost:6333/collections/nrg_research | python3 -m json.tool
```

Must show `vectors_count` > 0.

---

## Phase 4 — Test RAG Query

```bash
T1=$(curl -s -X POST http://localhost:8000/auth/login -H "Content-Type: application/json" -d '{"username":"researcher_user","password":"researcher-pass"}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")

curl -s -X POST http://localhost:8000/query -H "Authorization: Bearer $T1" -H "Content-Type: application/json" -d '{"question":"What are the latest trends in solar energy research?"}' | python3 -m json.tool | head -50
```

---

## Immortalize Phase

```
evidence/2026-04-25/critical_blockers/B5_vector_reingestion.log
```

Contents: ingestion method, vector count, RAG test result, time taken.

---

## Acceptance Criteria

- [ ] Qdrant collection has > 0 vectors
- [ ] RAG query returns relevant excerpts
- [ ] Backend health shows `qdrant_reachable: true`
- [ ] Evidence file B5 exists

---

## Rollback

If ingestion fails, stop and proceed with TP-B4 (Fast Path) for demo.
