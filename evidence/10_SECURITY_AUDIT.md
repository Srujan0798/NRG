# Security Audit Report — Session 92 (Guardian Agent)

**Date:** 2026-04-25
**Standard:** OWASP Top 10 + DPDP 2023
**Overall:** FAIL

---

## 🚨 CRITICAL (Exploit Possible)

### SQL Injection — Raw String Interpolation in Query Endpoint
**OWASP:** A03:2021 — Injection
**Severity:** 🚨 Critical
**File:** `src/api/main.py:479`

```python
sql_results = db.execute_query(
    f"SELECT * FROM researchers WHERE research_area LIKE '%{request.query.split()[0]}%' LIMIT 10",
    user_tier=user_tier,
)
```

**Exploit:** An attacker could send:
```json
{"query": "AI'%; DROP TABLE researchers; --"}
```
This would result in:
```sql
SELECT * FROM researchers WHERE research_area LIKE '%AI'; DROP TABLE researchers; --%' LIMIT 10
```

**Note:** `db.execute_query` may be dead code (class `NRGDatabase` is not defined in codebase — only `NRGDatabaseV2` is imported). But even if dead, this pattern should never exist in source code.

**Fix:**
```python
# Parameterized version:
sql_results = db.execute_query(
    "SELECT * FROM researchers WHERE research_area LIKE ? LIMIT 10",
    params=[f"%{request.query.split()[0]}%"],
    user_tier=user_tier,
)
```

---

### 2. SQL Injection — Same Pattern in RAG Fallback
**Severity:** 🚨 Critical
**File:** `src/api/main.py:470`

```python
retrieved = rag.retrieve(request.query, user_tier=user_tier, top_k=5)
```

**Check:** Verify `RAGSkill.retrieve()` uses parameterized queries internally for any SQL or search operations. If it does string formatting on the query, it's vulnerable.

**Fix:** Pass the raw query through `prompt_sanitiser.validate_query()` before passing to RAG. Already done at line 432 — but verify the RAG skill doesn't re-parse.

---

## ⚠️ HIGH (Data Exposure Risk)

### 3. Tier 3 (Industry) May See Researcher Emails
**OWASP:** A01:2021 — Broken Access Control
**Severity:** ⚠️ High
**File:** `src/api/main.py` (query endpoint)

The `_redact_pii_from_response()` function (line 53-111) scans response text for Aadhaar, PAN, phone, email patterns and replaces them with placeholders. But this is **text-based redaction** — if the LLM synthesizes a response containing an email address in a structured way, the regex might miss it.

More critically: the PII redaction happens **after** the LLM synthesizes. If the LLM includes PII in its synthesis, the regex-based approach may miss edge cases.

**Verification needed:** Test with `"query": "Give me the email addresses of all AI researchers in Gujarat"` as Tier 3 user.

### 4. Prompt Sanitiser — Bypass via Encoding?
**Severity:** ⚠️ High
**File:** `src/security/gateway/prompt_sanitiser.py`

**Check:** Does `classify_injection()` handle URL-encoded injection attempts? E.g., `%27` (single quote) instead of `'`?

**Fix needed:** URL-decode before classification:
```python
from urllib.parse import unquote
query = unquote(query)  # before classify_injection
```

---

## 📋 MEDIUM (Defense-in-Depth Gap)

### 5. Brute Force Protection Is In-Memory Only
**File:** `src/api/middleware/security.py`

`brute_force_protection._failure_count` is an in-memory dict. Multiple uvicorn workers (4 workers per `UVICORN_WORKERS=4`) each have their own copy. An attacker hitting different workers would not be blocked.

**Fix:** Use Redis for shared state across workers:
```python
# Redis-backed brute force
redis_client.incr(f"login_failures:{username}")
```

### 6. No CSRF Token on Non-GET Requests
**File:** `src/api/main.py` (all POST endpoints)

The API doesn't use CSRF tokens. It relies on `Authorization: Bearer <JWT>` header for auth. Since JWT is sent as a header (not a cookie), CSRF is mitigated. However, if refresh tokens are stored in cookies, CSRF is possible on `/auth/refresh`.

**Verification:** Check if refresh endpoint reads from cookie or body. If cookie → add CSRF token.

### 7. LLM Egress — No Content Length Limit on Responses
**File:** `src/api/main.py` (LLM call downstream)

The LLM response is streamed to the user. There's no max content length check — a malicious upstream LLM could send unbounded data.

**Fix:** Add max response size check in streaming handler.

---

## ✅ PASSED CHECKS

- ✅ No hardcoded secrets in source code
- ✅ JWT tokens have expiry enforced (`verify_exp: True`)
- ✅ `JWT_SECRET` raises error if not set (no fallback to empty string)
- ✅ `AUDIT_CHAIN_KEY` raises error in non-dev mode
- ✅ Prompt injection detection in `prompt_sanitiser.validate_query()`
- ✅ Rate limiting on login endpoint
- ✅ CORS configured with explicit origins
- ✅ Non-root user in `Dockerfile.api`
- ✅ HEALTHCHECK on both containers
- ✅ Token replay detection via `_jti_ip_registry`

---

## Recommendations

| Priority | Action | File |
|----------|--------|------|
| P0 | Fix SQL injection at line 479 — use parameterized queries | main.py:479 |
| P0 | Add URL decoding before injection classification | prompt_sanitiser.py |
| P1 | Test Tier 3 email exfiltration | main.py (test) |
| P1 | Redis-backed brute force protection | security.py |
| P2 | CSRF check on refresh endpoint | main.py |
| P2 | LLM response size limit | main.py |
