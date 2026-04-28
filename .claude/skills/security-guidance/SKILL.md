---
name: security-guidance
description: Real-time security pattern checking — warns about command injection, XSS, SQL injection, unsafe code patterns, secrets in code, and DPDP violations when editing files. NRG-specific: RBAC bypass, PII leakage, audit chain tampering.
model-agnostic: true
---

# Security Guidance

Run this scan whenever editing code that touches: auth, API endpoints, SQL generation, user input, LLM output, file operations, or environment variables.

## Trigger Patterns — Always Flag These

### 1. Command Injection
```python
# UNSAFE
os.system(f"convert {user_input}")
subprocess.call(f"grep {query}", shell=True)

# SAFE
subprocess.run(["convert", user_input], shell=False)
```
**Flag:** Any `shell=True` with user-controlled input. Any f-string in `os.system`, `eval`, `exec`.

### 2. SQL Injection (NRG-specific)
```python
# UNSAFE — LLM-generated SQL passed directly
query = llm_output["sql"]
db.execute(query)  # No validation

# SAFE — goes through validator
validated = sql_validator.validate(llm_output["sql"], allowlist=SCHEMA_ALLOWLIST)
db.execute(validated.safe_sql)
```
**Flag:** Any raw LLM SQL output executed without schema allowlist validation. See `src/security/egress_guard/`.

### 3. XSS
```typescript
// UNSAFE
element.innerHTML = userInput;
dangerouslySetInnerHTML={{ __html: apiResponse }}

// SAFE
element.textContent = userInput;
// or DOMPurify.sanitize(apiResponse)
```
**Flag:** `innerHTML`, `dangerouslySetInnerHTML` with any dynamic content.

### 4. Secrets in Code
```python
# UNSAFE
API_KEY = "sk-abc123..."
JWT_SECRET = "hardcoded-secret"

# SAFE
API_KEY = os.getenv("API_KEY")
```
**Flag:** Any string literal matching: `sk-`, `Bearer `, API key patterns, passwords, connection strings with credentials.

### 5. DPDP / PII Violations (NRG-critical)
```python
# UNSAFE — PII in LLM payload
payload = {"query": user_query, "schema": full_schema, "row": db_row}
llm.complete(payload)

# SAFE — only allowlisted schema fragments
payload = {"query": sanitized_query, "schema": egress_allowlist.filter(schema)}
llm.complete(payload)
```
**Flag:** Any LLM call containing raw DB rows, Aadhaar numbers, PAN, phone, email, full schema dumps.

### 6. RBAC Bypass (NRG-critical)
```python
# UNSAFE — tier check only in SQL, not in response shape
@app.get("/researchers")
def get_researchers(user = Depends(get_current_user)):
    return db.query(Researcher).all()  # No tier filtering

# SAFE — tier enforced at response shape layer
@app.get("/researchers")
def get_researchers(user = Depends(get_current_user)):
    results = db.query(Researcher).all()
    return response_filter.apply(results, user.tier)  # src/api/response_filter.py
```
**Flag:** Any endpoint returning data without calling `response_filter.apply()` or equivalent tier-shape enforcement.

### 7. Audit Chain Integrity
```python
# UNSAFE — bypasses audit
db.execute(sql)  # No audit event

# SAFE
result = db.execute(sql)
audit_logger.log_event(user_id, query, result_hash, tier)
```
**Flag:** Any database query in API handlers that doesn't log to the audit chain.

### 8. Path Traversal
```python
# UNSAFE
with open(f"data/{user_input}") as f: ...

# SAFE
safe_path = Path("data") / Path(user_input).name
if not safe_path.is_relative_to(Path("data")): raise ValueError
```
**Flag:** Any file open/read using unsanitized user input.

## Scan Checklist (run before every commit)

```
[ ] No shell=True with user input
[ ] No raw LLM SQL executed without validation
[ ] No innerHTML/dangerouslySetInnerHTML with dynamic content
[ ] No hardcoded secrets or API keys
[ ] No PII in LLM payloads
[ ] All API endpoints call response_filter.apply() for tier shaping
[ ] All DB queries in API handlers emit audit events
[ ] No path traversal via user-controlled filenames
[ ] No eval/exec on user input
[ ] JWT validation present on all protected endpoints
```

## NRG Security Layers (reference)

```
User input
  → PII detector (src/security/pii/)
  → Injection detector (src/security/injection/)
  → Schema allowlist (src/security/egress_guard/)
  → RBAC (src/auth/ + response_filter.py)
  → Audit chain (src/audit/)
  → DB co-sign (Postgres trigger)
```

If any layer is bypassed, flag immediately. These are not optional.
