# TP-B1 — FIX: Qdrant Vector DB Restart + Verify

**Owner:** DEVOPS / BACKEND  
**Estimated Duration:** 15–30 minutes  
**Blockers:** None  
**Priority:** P0 — Demo Killer

---

## Objective

Restart Qdrant and verify it is healthy, the collection exists, and all 19,323 vectors are accessible. RAG retrieval must work before any demo.

---

## Current State

- Qdrant is NOT running — `curl localhost:6333` returns `Connection refused`
- Health check shows: `qdrant_reachable: false`, `vectors_indexed: 0`
- Previous state: 19,323 vectors, 384-dim, collection `nrg_research`

---

## Fortify Phase (Diagnose)

1. Check if Qdrant was running via Docker:
   ```bash
   docker ps -a | grep -i qdrant
   ```

2. Check if Qdrant binary exists:
   ```bash
   which qdrant
   ls /usr/local/bin/qdrant 2>/dev/null
   ls /opt/qdrant 2>/dev/null
   ```

3. Check for Qdrant storage directory:
   ```bash
   find /Users/srujansai/Desktop/NRG -name "*qdrant*" -type d 2>/dev/null
   find ~ -name "qdrant_storage" 2>/dev/null | head -5
   ```

4. Check shell history for how Qdrant was started before:
   ```bash
   history | grep -i qdrant | tail -10
   ```

---

## Elevate Phase (Fix)

### Path A: Docker (Most Likely)

If `docker ps -a` shows a qdrant container:
```bash
# Start existing container
docker start qdrant

# Or if container name is different:
docker start $(docker ps -a -q -f ancestor=qdrant/qdrant)

# Verify:
curl -s http://localhost:6333
```

If no container exists, create one:
```bash
# With persistent storage mapped to project directory
docker run -d \
  --name qdrant \
  -p 6333:6333 \
  -v /Users/srujansai/Desktop/NRG/qdrant_storage:/qdrant/storage \
  qdrant/qdrant

# Wait 10 seconds for startup
sleep 10
curl -s http://localhost:6333
```

### Path B: Binary / Homebrew

If Qdrant was installed via Homebrew:
```bash
brew services start qdrant
# or
qdrant --storage-path /path/to/qdrant_storage &
```

### Path C: No Previous Install

If Qdrant was never installed, install it:
```bash
# Via Docker (recommended)
docker run -d --name qdrant -p 6333:6333 qdrant/qdrant

# Or via Homebrew
brew install qdrant/tap/qdrant
brew services start qdrant
```

**WARNING:** If Qdrant was previously running but storage was not persisted, the 19,323 vectors may be lost and need to be re-ingested. Check if storage directory exists first.

---

## Immortalize Phase (Verify)

1. **Health check via API:**
   ```bash
   curl -s http://localhost:6333
   ```
   Must return JSON with cluster info.

2. **Collection check:**
   ```bash
   curl -s http://localhost:6333/collections/nrg_research
   ```
   Must show collection exists.

3. **Vector count:**
   ```bash
   curl -s http://localhost:6333/collections/nrg_research | python3 -c "import sys,json; d=json.load(sys.stdin); print('Vectors:', d['result']['vectors_count'])"
   ```
   Must show ~19,323 vectors.

4. **Backend health check:**
   ```bash
   curl -s http://localhost:8000/health | python3 -c "import sys,json; d=json.load(sys.stdin); print('Qdrant:', d['retriever']['qdrant_reachable'], 'Vectors:', d['retriever']['vectors_total'])"
   ```
   Must show `qdrant_reachable: true` and vectors > 0.

5. **RAG test query:**
   ```bash
   curl -s -X POST http://localhost:8000/query \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"question":"research on solar energy"}' 2>/dev/null | head -200
   ```
   Must return a response (not 500, not empty).

6. Save evidence:
   ```
   evidence/2026-04-25/critical_blockers/B1_qdrant_fix.log
   ```
   Contents: Qdrant version, collection status, vector count, backend health output.

---

## Acceptance Criteria

- [ ] `curl http://localhost:6333` responds with JSON
- [ ] Collection `nrg_research` exists
- [ ] Vector count ≥ 1 (ideally ~19,323)
- [ ] Backend health shows `qdrant_reachable: true`
- [ ] RAG query returns a response without 500 error
- [ ] Evidence file B1 exists with verification output

---

## Rollback Plan

If Qdrant cannot be started or vectors are lost:
- Document the loss in evidence file
- Escalate to Founder — may need to re-run ingestion scripts
- Do NOT demo with RAG until vectors are restored
