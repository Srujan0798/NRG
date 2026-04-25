# TP-B3 — FULL STACK RESTART: Qdrant + Backend + Lockouts

**Owner:** DEVOPS / BACKEND  
**Estimated Duration:** 20–30 minutes  
**Blockers:** None  
**Priority:** P0 — Everything depends on this

---

## Objective

Restart the entire stack cleanly: Qdrant vector DB, backend API with `.env` loaded, and reset all login lockouts. Verify Minimax cloud synthesis works end-to-end.

---

## Phase 1 — KILL EVERYTHING (Clean Slate)

```bash
cd /Users/srujansai/Desktop/NRG

# 1. Kill all uvicorn processes
pkill -f uvicorn
sleep 3

# 2. Verify no uvicorn remains
ps aux | grep uvicorn | grep -v grep
# If any remain: kill -9 <PID>

# 3. Stop Qdrant (if running via Docker)
docker stop qdrant 2>/dev/null
docker stop nrg-qdrant 2>/dev/null
sleep 2

# 4. Verify nothing on ports 8000 or 6333
lsof -i :8000 2>/dev/null | grep LISTEN || echo "Port 8000 clear"
lsof -i :6333 2>/dev/null | grep LISTEN || echo "Port 6333 clear"
```

---

## Phase 2 — START QDRANT

```bash
cd /Users/srujansai/Desktop/NRG

# Option A: Start existing Docker container
docker start qdrant 2>/dev/null || docker start nrg-qdrant 2>/dev/null

# Option B: If no container exists, create one
docker run -d \
  --name qdrant \
  -p 6333:6333 \
  -v /Users/srujansai/Desktop/NRG/qdrant_storage:/qdrant/storage \
  qdrant/qdrant:v1.11.3

# Wait for startup
sleep 10

# Verify Qdrant is healthy
curl -s http://localhost:6333 | python3 -m json.tool

# Verify collection exists
curl -s http://localhost:6333/collections/nrg_research | python3 -m json.tool
```

**If Qdrant starts but collection is missing:**
```bash
# Check if storage was persisted
ls /Users/srujansai/Desktop/NRG/qdrant_storage/ 2>/dev/null || echo "No local storage"

# If no vectors, you may need to re-ingest
docker logs qdrant --tail 20
```

---

## Phase 3 — RESET LOGIN LOCKOUTS

Lockouts may be in-memory (cleared by killing uvicorn) or in SQLite.

```bash
cd /Users/srujansai/Desktop/NRG

# Check if any login_attempts table exists
sqlite3 nrg_research.db ".tables" 2>/dev/null | tr ' ' '\n' | grep -i "login\|attempt\|lock"

# If a table exists, clear it (example table names):
# sqlite3 nrg_research.db "DELETE FROM login_attempts;"
# sqlite3 nrg_research.db "DELETE FROM brute_force_attempts;"
# sqlite3 nrg_research.db "DELETE FROM auth_lockouts;"

# If no table exists, lockouts are in-memory and were cleared by killing uvicorn
```

**Verify correct credentials from `.env`:**
```bash
grep -E "RESEARCHER_PASSWORD|GOV_PASSWORD|INDUSTRY_PASSWORD" .env
```

Expected:
- researcher_user / `researcher-pass`
- gov_user / `government-pass`
- industry_user / `industry-pass`

---

## Phase 4 — START BACKEND WITH ENV VARS

```bash
cd /Users/srujansai/Desktop/NRG

# Load .env into current shell, then start uvicorn
set -a
source .env
set +a

# Verify Minimax env is loaded
echo "LLM_PROVIDER=$LLM_PROVIDER"
echo "LLM_FALLBACK_ORDER=$LLM_FALLBACK_ORDER"
echo "CLOUD_SYNTHESIS_ALLOWED=$CLOUD_SYNTHESIS_ALLOWED"
echo "MINIMAX_API_KEY=${MINIMAX_API_KEY:0:20}..."

# Start backend
.venv/bin/python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000 &

# Wait for startup
sleep 5

# Verify health
curl -s http://localhost:8000/health | python3 -m json.tool
```

**Health check must show:**
- `qdrant_reachable: true`
- `vectors_total` > 0
- No errors

---

## Phase 5 — VERIFY END-TO-END

### 5.1 Login All 3 Tiers

```bash
# Tier 1 — Researcher
T1=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"researcher_user","password":"researcher-pass"}' | \
  python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")
echo "T1 token: ${T1:0:30}..."

# Tier 2 — Government
T2=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"gov_user","password":"government-pass"}' | \
  python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")
echo "T2 token: ${T2:0:30}..."

# Tier 3 — Industry
T3=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"industry_user","password":"industry-pass"}' | \
  python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")
echo "T3 token: ${T3:0:30}..."
```

### 5.2 Run Query and Check Synthesizer

```bash
# Run a query and capture full response
curl -s -X POST http://localhost:8000/query \
  -H "Authorization: Bearer $T1" \
  -H "Content-Type: application/json" \
  -d '{"question":"Top 5 funding agencies by grant amount"}' | \
  python3 -m json.tool | tee /tmp/query_response.json

# Check what the response looks like
echo "=== RESPONSE PREVIEW ==="
head -50 /tmp/query_response.json
```

**What to look for:**
- Response is natural language prose (not ASCII table, not raw JSON dict)
- Response includes citations `[cite:...]`
- No error messages
- Response time < 15 seconds

### 5.3 Check Backend Logs for Minimax Usage

```bash
# In another terminal, or check logs file
tail -100 logs/api_server.log | grep -i "minimax\|synthesizer\|sovereign\|mesh\|rule_based"
```

**What to look for:**
- `✅ LLM Mesh: minimax client initialized` — Minimax loaded
- `Using SovereignLLMMesh for synthesis` — Mesh is active
- NOT `Using rule-based template synthesis` — unless mesh failed

---

## Phase 6 — IF MINIMAX FAILS

If the synthesizer still falls back to rule-based, check:

```bash
# Check if Minimax client initialized
tail -50 logs/api_server.log | grep "minimax"

# Common failures:
# 1. "MINIMAX_API_KEY is required" → Key not loaded from .env
# 2. "MinimaxLLMClient" timeout → API slow/unreachable
# 3. "Circuit breaker OPEN" → Too many failures, wait 30s

# Test Minimax directly
curl -s -X POST https://api.minimaxi.chat/v1/text/chatcompletion_v2 \
  -H "Authorization: Bearer $MINIMAX_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"minimax-m2.7","messages":[{"role":"user","content":"Hello"}]}' | \
  head -c 200
```

If Minimax API test fails, the API key may be expired/invalid.

---

## Immortalize Phase (Evidence)

Save all verification output:

```
evidence/2026-04-25/critical_blockers/B3_full_restart_verification.log
```

Contents must include:
1. Qdrant health response
2. Backend health response (showing qdrant_reachable: true)
3. All 3 login tokens obtained successfully
4. Query response preview (first 50 lines)
5. Backend log snippet showing Minimax initialization
6. If Minimax works: "Cloud synthesis: ACTIVE"
7. If Minimax fails: exact error message + fallback status

---

## Acceptance Criteria

- [ ] Qdrant responding on `localhost:6333`
- [ ] Backend health shows `qdrant_reachable: true`
- [ ] All 3 tiers can login (tokens obtained)
- [ ] Query returns a response in < 15 seconds
- [ ] Response is readable prose (not ASCII table)
- [ ] Backend logs show Minimax client initialized
- [ ] Evidence file B3 exists with verification output

---

## Rollback Plan

If restart breaks everything:
```bash
pkill -f uvicorn
docker stop qdrant
# Previous state was already broken, so no worse off
# Debug logs and try again
```
