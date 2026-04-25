# TP-B2 — FIX: Reset Login Lockouts + Verify All 3 Tiers

**Owner:** BACKEND / SECURITY  
**Estimated Duration:** 15–30 minutes  
**Blockers:** None  
**Priority:** P0 — Demo Killer

---

## Objective

Reset all brute-force lockouts, verify correct passwords for all 3 persona tiers, and confirm each tier can login and query successfully.

---

## Current State

- `researcher_user` — **LOCKED** for ~835 seconds due to brute-force protection
- `gov_user` — password was wrong in previous attempts (correct is `government-pass`)
- `industry_user` — password is `industry-pass`
- Previous "brute force reset" may have been temporary or only affected one account

---

## Fortify Phase (Diagnose)

1. Check how lockouts are stored:
   ```bash
   grep -r "lockout\|brute\|attempt" /Users/srujansai/Desktop/NRG/src/auth/ 2>/dev/null | grep -v __pycache__ | head -10
   ```

2. Check SQLite database for lockout table:
   ```bash
   sqlite3 /Users/srujansai/Desktop/NRG/nrg_research.db ".tables" 2>/dev/null | tr ' ' '\n' | grep -i "login\|lock\|attempt\|user"
   ```

3. Check if lockouts are in-memory (Redis) or file-based:
   ```bash
   grep -r "redis\|in_memory\|dict.*attempt" /Users/srujansai/Desktop/NRG/src/auth/ 2>/dev/null | grep -v __pycache__ | head -10
   ```

---

## Elevate Phase (Fix)

### Step 1: Find and Reset Lockouts

**If lockouts are in SQLite:**
```bash
sqlite3 /Users/srujansai/Desktop/NRG/nrg_research.db
# Then run:
# .tables
# SELECT * FROM login_attempts;  -- or whatever the table is called
# DELETE FROM login_attempts WHERE username = 'researcher_user';
# .quit
```

**If lockouts are in-memory (Python dict):**
- Restart the backend API server — in-memory lockouts will clear
```bash
# Find and kill existing uvicorn processes
pkill -f uvicorn
sleep 2
# Restart
.venv/bin/python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000
```

**If lockouts are in Redis:**
```bash
# Check Redis keys
redis-cli KEYS "*lockout*" 2>/dev/null
redis-cli KEYS "*attempt*" 2>/dev/null
# Delete lockout keys
redis-cli DEL "lockout:researcher_user" 2>/dev/null
```

### Step 2: Verify Correct Passwords

From `src/auth/jwt_handler.py`, the defaults are:

| Username | Default Password | Env Var Override |
|----------|-----------------|------------------|
| researcher_user | `researcher-pass` | `RESEARCHER_PASSWORD` |
| gov_user | `government-pass` | `GOV_PASSWORD` |
| industry_user | `industry-pass` | `INDUSTRY_PASSWORD` |

Test each:
```bash
for user in researcher_user gov_user industry_user; do
  case $user in
    researcher_user) pass="researcher-pass" ;;
    gov_user) pass="government-pass" ;;
    industry_user) pass="industry-pass" ;;
  esac
  echo "=== Testing $user ==="
  curl -s -X POST http://localhost:8000/auth/login \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$user\",\"password\":\"$pass\"}" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print('OK' if 'access_token' in d else d)"
done
```

### Step 3: Verify Query Works for Each Tier

Get tokens first:
```bash
T1=$(curl -s -X POST http://localhost:8000/auth/login -H "Content-Type: application/json" -d '{"username":"researcher_user","password":"researcher-pass"}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")
T2=$(curl -s -X POST http://localhost:8000/auth/login -H "Content-Type: application/json" -d '{"username":"gov_user","password":"government-pass"}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")
T3=$(curl -s -X POST http://localhost:8000/auth/login -H "Content-Type: application/json" -d '{"username":"industry_user","password":"industry-pass"}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")
```

Test query per tier:
```bash
for tier in T1 T2 T3; do
  token=$(eval echo "\$$tier")
  echo "=== $tier ==="
  curl -s -X POST http://localhost:8000/query \
    -H "Authorization: Bearer $token" \
    -H "Content-Type: application/json" \
    -d '{"question":"Top funding agencies"}' 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print('Status:', 'OK' if 'answer' in d or 'result' in d else d)"
done
```

---

## Immortalize Phase (Verify)

1. Save verification output:
   ```
   evidence/2026-04-25/critical_blockers/B2_login_verification.log
   ```

2. Contents must include:
   - Login test for all 3 tiers (PASS/FAIL per tier)
   - Query test for all 3 tiers (PASS/FAIL per tier)
   - Lockout reset method used
   - Correct password table for reference

3. Update `frontend/src/components/Login.tsx` if the seeded credentials there are wrong:
   - Check `PERSONA_CREDENTIALS` object
   - Ensure it matches the actual passwords (`researcher-pass`, `government-pass`, `industry-pass`)

---

## Acceptance Criteria

- [ ] All 3 tiers can login successfully with correct passwords
- [ ] All 3 tiers can run a query and get a response
- [ ] No account is locked or blocked
- [ ] Frontend `PERSONA_CREDENTIALS` matches backend passwords
- [ ] Evidence file B2 exists with verification output

---

## Rollback Plan

If lockouts cannot be reset:
- Create new test accounts with guaranteed passwords
- Or modify auth middleware to bypass lockout check for demo accounts (temporary, document it)
- Or restart backend (if in-memory) and use correct passwords on first attempt
