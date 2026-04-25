# TP-B4 — FAST PATH: Start Backend, Verify Text-to-SQL Demo

**Owner:** BACKEND  
**Estimated Duration:** 10–15 minutes  
**Blockers:** TP-B3 (Qdrant must be running)  
**Priority:** P0 — Get demo working NOW

---

## Objective

Start the backend with `.env` loaded, verify all 3 tiers can login and run Text-to-SQL queries, verify Minimax synthesis produces prose. Skip RAG — it will fail because Qdrant has no vectors. This gets the demo working in 10 minutes.

---

## Phase 1 — Start Backend

```bash
cd /Users/srujansai/Desktop/NRG

# Load env vars into shell
set -a
source .env
set +a

# Verify Minimax config is loaded
echo "Provider: $LLM_PROVIDER"
echo "Fallback: $LLM_FALLBACK_ORDER"
echo "Cloud allowed: $CLOUD_SYNTHESIS_ALLOWED"

# Start backend
.venv/bin/python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000 &

# Wait for startup
sleep 5

# Verify health
curl -s http://localhost:8000/health | python3 -m json.tool
```

**Health check must show:**
- `status: "healthy"`
- `qdrant_reachable: false` or `vectors_total: 0` — EXPECTED (we know Qdrant is empty)
- No errors in database or audit sections

---

## Phase 2 — Verify Login

```bash
# Tier 1 — Researcher
curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"researcher_user","password":"researcher-pass"}' | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print('T1:', 'OK' if 'access_token' in d else d)"

# Tier 2 — Government
curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"gov_user","password":"government-pass"}' | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print('T2:', 'OK' if 'access_token' in d else d)"

# Tier 3 — Industry
curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"industry_user","password":"industry-pass"}' | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print('T3:', 'OK' if 'access_token' in d else d)"
```

All 3 must return `OK`.

---

## Phase 3 — Verify Text-to-SQL + Minimax Synthesis

```bash
# Get Tier 1 token
T1=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"researcher_user","password":"researcher-pass"}' | \
  python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")

# Run a SQL query (structured, should NOT need RAG)
curl -s -X POST http://localhost:8000/query \
  -H "Authorization: Bearer $T1" \
  -H "Content-Type: application/json" \
  -d '{"question":"Which institutes received the highest government grants in 2023?"}' | \
  python3 -m json.tool | tee /tmp/sql_query_response.json
```

**What to verify:**
- Response is natural language (not ASCII table)
- Response time < 15 seconds
- No 500 error
- Backend logs show Minimax being used

Check logs:
```bash
tail -50 logs/api_server.log | grep -i "minimax\|synthesizer\|mesh\|rule_based"
```

**If Minimax works:** You see `Using SovereignLLMMesh for synthesis` and the response is prose.
**If Minimax fails:** It falls back to rule-based. Check logs for error.

---

## Phase 4 — Verify Tier Differentiation

Run the SAME query for Tier 1 and Tier 3. Responses should differ.

```bash
T3=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"industry_user","password":"industry-pass"}' | \
  python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")

echo "=== TIER 1 RESPONSE ==="
curl -s -X POST http://localhost:8000/query \
  -H "Authorization: Bearer $T1" \
  -H "Content-Type: application/json" \
  -d '{"question":"Top 5 funding agencies"}' | python3 -m json.tool | head -30

echo ""
echo "=== TIER 3 RESPONSE ==="
curl -s -X POST http://localhost:8000/query \
  -H "Authorization: Bearer $T3" \
  -H "Content-Type: application/json" \
  -d '{"question":"Top 5 funding agencies"}' | python3 -m json.tool | head -30
```

---

## Phase 5 — Test PII Block

```bash
curl -s -X POST http://localhost:8000/query \
  -H "Authorization: Bearer $T1" \
  -H "Content-Type: application/json" \
  -d '{"question":"Show researchers with Aadhaar 1234 5678 9012"}' | \
  python3 -m json.tool
```

Must return a clean blocked message, not a stack trace.

---

## Immortalize Phase (Evidence)

```
evidence/2026-04-25/critical_blockers/B4_fast_path_verification.log
```

Contents:
1. Backend health check output
2. All 3 login results (PASS/FAIL)
3. SQL query response preview (first 50 lines)
4. Backend log snippet showing Minimax or fallback
5. Tier 1 vs Tier 3 response comparison
6. PII block response
7. Final verdict: `DEMO READY (SQL only) / NOT READY`

---

## Acceptance Criteria

- [ ] Backend running on port 8000
- [ ] All 3 tiers login successfully
- [ ] Text-to-SQL query returns natural language response
- [ ] Tier 1 and Tier 3 show different responses for same query
- [ ] PII query is blocked with clean message
- [ ] Evidence file B4 exists

---

## Known Limitations (Document These)

- RAG queries will fail or return empty — Qdrant has no vectors
- Step 9 of demo script (knowledge graph) will not work
- Any query requiring paper/abstract search will not work

**Mitigation for demo:** Only demo SQL-based queries. Skip RAG-dependent features.
