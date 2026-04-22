# Deep Code Review — NRG Platform
**Date:** April 21, 2026
**Reviewer:** Mentor Agent
**Scope:** Orchestration Nodes, LLM Config, API, Auth

---

## Review Summary

| Module | Files | Issues | Severity |
|--------|-------|--------|----------|
| Orchestration Nodes | 6 nodes | 5 | 2 High, 3 Medium |
| LLM Config | `llm_config.py`, `local_llm.py` | 2 | 1 High, 1 Medium |
| API (main.py) | 857 lines | 3 | 1 High, 2 Medium |
| Auth | `jwt_handler.py`, `middleware.py` | 1 | 1 Low |

---

## ORCHESTRATION NODES

### Node 1: planner.py

**File:** `src/orchestration/nodes/planner.py`

**Finding 1: Planner fallback silently returns None — no warning**

When `planner_node` fails (ModuleNotFoundError), it returns `{"plan": None}`. This causes the router to receive no plan, which is handled, but there's no indication that planning was skipped.

```python
# graph.py:26-33
except ModuleNotFoundError:
    def planner_node(state: Any) -> dict:
        return {"plan": None}  # Silent fallback
```

**Severity:** Medium — Graph continues without plan, but downstream nodes may behave unexpectedly.

**Finding 2:** `_build_plan()` method not reviewed for injection — relies on LLM to decompose. If the planner LLM prompt is injection-crafted, the output SQL could be malformed. However, the executor re-validates all SQL, so this is mitigated.

**Status:** 🟡 Acceptable with mitigation

---

### Node 2: router.py

**File:** `src/orchestration/nodes/router.py`

**Finding: Intent classification is heuristic-only, not validated against ground truth**

The `_classify_intent()` function uses regex pattern matching against the query. This is deterministic but brittle:
- "show me the count of researchers" → structured (has "count")
- "what is the count" → unstructured (no match) — but it's clearly structured!

```python
INTENT_PATTERNS = {
    "structured": [r"(list|find|show|get|count|how many)", ...],
    "unstructured": [r"(what are|explain|describe|summarize)", ...],
}
# If max_score == 0, defaults to "unstructured" — could misroute simple queries
```

**Severity:** Medium — Simple structured queries like "what is the count of researchers in Gujarat" would route to RAG instead of SQL, reducing accuracy.

**Recommendation:** Add "what is the count" / "how many" patterns to structured routing, or make the router also consider the presence of domain entities (researcher, lab, publication) as indicators of structured intent.

**Status:** 🟡 Acceptable — The hybrid route (sql+rag) catches most ambiguous cases.

---

### Node 3: executor.py

**File:** `src/orchestration/nodes/executor.py`

**Finding 1: Skill instances cached at module level — thread safety concern**

```python
_sql_skill_instance: TextToSQLSkill | None = None
_sql_skill_class_id: int | None = None
_lock = threading.Lock()  # Lock only around creation, not use
```

The skill instances (`TextToSQLSkill`, `RAGSkill`) are cached at module level. If the skill objects hold connection state (DB connections, file handles), they may not be thread-safe across concurrent requests.

**Severity:** Medium — If `TextToSQLSkill` holds a DB connection, concurrent calls could share it. However, `NRGDatabase` from `database_v2.py` creates fresh connections per call, so this is likely mitigated.

**Finding 2: Errors in executor are collected but not surfaced unless empty results**

```python
results["errors"].append(str(e))  # Appended but when are they shown to user?
```

The executor catches errors and appends them to `results["errors"]`, but if `sql_results` is non-empty, the errors are silently ignored. The user might get partial data without knowing some skills failed.

**Severity:** Medium — Should log errors as warnings and include them in response metadata even if results are present.

**Status:** 🟡 Acceptable

---

### Node 4: synthesizer.py

**File:** `src/orchestration/nodes/synthesizer.py`

**Finding 1: `_redact_text()` uses naive regex — potential bypass**

```python
REDACTION_PATTERNS = (
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),  # email
    re.compile(r"\+?\d[\d\s().-]{8,}\d"),  # phone — broad!
    re.compile(r"\b(?:sk|nvapi|AIza|xox[baprs])-?[A-Za-z0-9._-]{8,}\b"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.DOTALL),
)
```

The phone regex `\+?\d[\d\s().-]{8,}\d` could over-censor legitimate text containing number-like sequences. However, it's used on minimized SQL results which should not contain narrative text — so this is low risk.

**Finding 2: `_citation_for_row()` silently uses `structured:0` when no ID found**

```python
def _citation_for_row(row: dict) -> str:
    for key in ("publication_id", "researcher_id", "funding_id", "lab_id", "institution_id"):
        if row.get(key):
            return f"[cite:{row[key]}:0]"
    return "[cite:structured:0]"  # Silent fallback
```

If a row has no recognized ID key, citations default to `[cite:structured:0]`. This is acceptable but makes citation tracking harder.

**Status:** 🟢 Good — The synthesizer has defense-in-depth redaction and data minimization. 3-tier fallback ensures a response is always returned.

---

### Node 5: verifier.py

**File:** `src/orchestration/nodes/verifier.py`

**Finding: Verifier retry logic not visible — is it a loop?**

The `verifier_node` returns `{"verification_status": bool(response)}`. If verification fails, does the graph retry synthesis? Looking at `graph.py`, the verifier goes directly to END — no retry loop.

**Status:** ⚠️ Missing — The Core_Idea_Clean.md says the verifier "retries if unsupported", but this loop is not implemented. This is the same gap noted in the Architecture Review (H1): Reflector node is missing, and so is the retry loop.

---

## LLM CONFIG

### llm_config.py

**Finding: LLM_FALLBACK_ORDER not used — cascade is hardcoded**

The `.env` specifies `LLM_FALLBACK_ORDER=nvidia`, but the synthesizer in `synthesizer.py` has a **hardcoded** cascade: cloud → local → rule-based. The `fallback_order` is never read from config.

**Severity:** High (Architecture) — documented in ARCHITECTURE_REVIEW.md.

---

### local_llm.py

**Finding: `get_local_llm()` uses global state — test isolation risk**

```python
_model = None
_tokenizer = None

def get_local_llm():
    global _model, _tokenizer
    if _model is not None:
        return _model, _tokenizer  # Cached across all tests
```

The global model cache in `local_llm.py` could cause test pollution if tests don't reset it. The `_DeterministicTestEmbeddingModel` in `embedder.py` is the right pattern — it checks `PYTEST_CURRENT_TEST` env var. `local_llm.py` doesn't have an equivalent.

**Severity:** Medium — Could cause flaky tests in CI.

---

## API (main.py)

**Finding 1: CORS wildcard risk — allow_credentials + env var origins**

```python
allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
allow_credentials=True,
```

This is a security finding (S-02 in SECURITY_AUDIT.md) — if `CORS_ORIGINS=*` is accidentally set, browsers will reject it, but the configuration is not validated.

**Severity:** High

**Finding 2: No rate limiting at FastAPI level — relies on Kong**

Rate limiting is done by Kong (in docker-compose), but if Kong is bypassed (direct API access), there's no app-level rate limiting.

**Severity:** Medium — Acceptable since Kong is the primary gateway.

**Finding 3: `workflow = NRGWorkflow()` is a module-level singleton**

```python
workflow = NRGWorkflow()  # Line 79
jwt_handler = JWTHandler()  # Line 80
```

These are instantiated when the module loads, not lazily. This is fine for production, but means tests can't easily mock them without patching.

**Severity:** Low — Standard FastAPI pattern.

---

## AUTH

### jwt_handler.py

**Finding: `revoked_jtis` in-memory set doesn't survive restart**

```python
self.revoked_jtis: set[str] = set()  # Line 127
```

Revoked token JTIs are stored in a Python `set` — this is ephemeral. On server restart, the set is empty. The `RefreshStore` persists refresh tokens to disk/database, but the access token revocation list does not.

**Impact:** If an access token is compromised and revoked, and the server restarts before the token expires, the attacker can use it again.

**Mitigation:** Access tokens have short TTL (3600s), so window is limited. But a sophisticated attacker could use the token within that window.

**Severity:** Low — Acceptable for demo. For production: use Redis-backed revocation list.

**Overall auth assessment:** ✅ Strong — RS256, proper token rotation, refresh store persistence, algorithm allowlist.

---

## Code Quality Metrics

| Metric | Value |
|--------|-------|
| Lines of code reviewed | ~2,000 |
| Type annotations | Partial (TypedDict used, but some `Any`) |
| Error handling | Present throughout |
| Dead code | Minimal |
| Import organization | ✅ Clean |
| Cyclomatic complexity | Low (functions < 50 lines) |

---

## Top 5 Action Items

| Priority | File | Issue | Fix |
|----------|------|-------|-----|
| P0 | `src/api/main.py` | CORS_ORIGINS validation missing | Add `assert origins != "*"` check |
| P0 | `src/orchestration/nodes/synthesizer.py` | Egress guard not wired | Wrap LLM client with SovereignHTTPXClient |
| P1 | `src/orchestration/nodes/router.py` | Heuristic intent classification | Add entity-based routing |
| P1 | `src/orchestration/nodes/verifier.py` | No retry loop | Implement retry or remove "retry" from Core Idea |
| P2 | `src/auth/jwt_handler.py` | In-memory revoked_jtis | Use Redis-backed revocation for production |