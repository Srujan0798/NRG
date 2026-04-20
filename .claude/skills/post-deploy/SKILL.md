---
name: post-deploy
description: Post-deployment smoke test and health verification. Use /post-deploy [environment] to run after any deployment.
allowed-tools: Bash(curl *) Bash(docker *) Bash(docker-compose *) Bash(.venv/bin/python *) Read
---

# Post-Deploy Verification

Run after every deployment to verify the system is healthy.

## Smoke Tests

### 1. Health Endpoints
```bash
API_URL=${ARGUMENTS:-http://localhost:8000}

echo "=== Health Checks ==="
curl -sf "$API_URL/health" | python3 -m json.tool || echo "FAIL: /health"
curl -sf "$API_URL/health/db" | python3 -m json.tool || echo "FAIL: /health/db"
curl -sf "$API_URL/health/llm" | python3 -m json.tool || echo "FAIL: /health/llm"
curl -sf "$API_URL/health/qdrant" | python3 -m json.tool || echo "FAIL: /health/qdrant"
```

### 2. Auth Flow
```bash
echo "=== Auth Flow ==="
# Login as each persona
for user in '{"username":"researcher_user","password":"researcher-pass"}' '{"username":"gov_user","password":"government-pass"}' '{"username":"industry_user","password":"industry-pass"}'; do
    TOKEN=$(curl -sf -X POST "$API_URL/login" -H "Content-Type: application/json" -d "$user" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token','FAIL'))")
    echo "Login: $(echo $user | python3 -c "import sys,json; print(json.load(sys.stdin)['username'])") → ${TOKEN:0:20}..."
done
```

### 3. Query Pipeline
```bash
echo "=== Query Pipeline ==="
TOKEN=$(curl -sf -X POST "$API_URL/login" -H "Content-Type: application/json" -d '{"username":"researcher_user","password":"researcher-pass"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
curl -sf -X POST "$API_URL/query" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"query":"researchers in AI in Maharashtra"}' | python3 -c "import sys,json; r=json.load(sys.stdin); print(f'Response length: {len(str(r))} chars'); print(f'Has response: {bool(r.get(\"response\") or r.get(\"synthesized_response\"))}')"
```

### 4. Audit Chain
```bash
echo "=== Audit Chain ==="
curl -sf "$API_URL/audit/verify" -H "Authorization: Bearer $TOKEN" | python3 -m json.tool || echo "FAIL: audit verify"
```

## Output
```
POST-DEPLOY REPORT — [environment]
  [UP/DOWN] Health endpoints
  [PASS/FAIL] Auth flow (3 personas)
  [PASS/FAIL] Query pipeline
  [PASS/FAIL] Audit chain
  
VERDICT: DEPLOYMENT HEALTHY / ISSUES DETECTED
```
