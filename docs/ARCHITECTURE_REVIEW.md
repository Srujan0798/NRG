# NRG Architecture Review
**Date:** April 21, 2026
**Status:** Internal Review
**Reviewer:** Architecture Review (Sprint H)

---

## Executive Summary

**Overall Architecture Health: 🟡 Yellow (At Risk)**

The NRG platform has a solid architectural foundation with the 6-node pipeline, tier-based RBAC, and sovereignty egress guard all implemented. However, there are critical gaps: the Reflector node is missing from the pipeline, the LLM cascade doesn't properly respect `LLM_FALLBACK_ORDER`, and RBAC enforcement in the synthesizer is incomplete. Most critically, the Reflector node — the 6th node described in the Core Idea — is not implemented, making the pipeline a 5-node pipeline. These issues are addressable without architectural changes.

| Component | Status | Severity |
|-----------|--------|----------|
| 6-Node Pipeline | 🟡 5/6 (Reflector missing) | Medium |
| LLM Cascade Failover | 🟡 Partial (fallback_order ignored) | Medium |
| Auth/RBAC Tier Isolation | 🟡 Partial (middleware not wired) | High |
| Data Sovereignty Enforcement | ✅ Strong (egress guard + redaction) | Low |
| SQLite → PostgreSQL Migration | 🟡 Planned (migrations exist) | Medium |

---

## 1. Six-Node Pipeline Design Validation

### Finding: 5 of 6 Nodes Implemented — Reflector Missing

The Core_Idea_Clean.md describes a 6-node pipeline:
```
receiver → planner → router → executor → synthesizer → verifier → reflector → END
```

The actual implementation in `src/orchestration/graph.py` has only 5 active nodes:
- ✅ `receiver` — assigns session ID, loads conversation history
- ✅ `planner` — decomposes queries (with fallback to no-op)
- ✅ `router` — classifies intent (structured/unstructured/hybrid)
- ✅ `executor` — runs Text-to-SQL and/or RAG
- ✅ `synthesizer` — LLM synthesis with 3-tier cascade
- ✅ `verifier` — citation faithfulness checking
- ❌ `reflector` — **NOT IMPLEMENTED**

The `verifier` node does not feed back into the graph. There is no "reflect on the response quality" loop. This is listed in Core_Idea_Clean.md as the 6th node.

**Impact:** Medium. The pipeline works end-to-end, but there is no self-reflection loop for response quality improvement. The Core Idea says the Reflector "evaluates synthesis quality and decides if re-generation is needed" — this logic does not exist.

**Recommendation:** Either implement the Reflector node or update Core_Idea_Clean.md to reflect the actual 5-node pipeline. The Reflector's logic could be added as a conditional loop-back in the graph, re-running the synthesizer with stricter prompts if verification fails.

### Node State Management: ✅ Correct

Each node receives `NRGState` and returns partial dict updates. The state is properly typed in `src/orchestration/state.py`. No state leakage between nodes.

### Error Handling: ✅ Present

Each node has try/except with fallback behavior:
- `planner_node` → returns `{"plan": None}` on failure
- `verifier_node` → returns `{"verification_status": bool(response)}` on failure
- `executor_node` → catches skill failures, appends to `errors` list
- `synthesizer_node` → 3-tier cascade ensures a response is always returned

---

## 2. LLM Mesh Failover Correctness

### Finding: Cascade Order Is Hardcoded, `LLM_FALLBACK_ORDER` Is Ignored

**The .env specifies:**
```
LLM_PROVIDER=nvidia
LLM_FALLBACK_ORDER=nvidia
CLOUD_SYNTHESIS_ALLOWED=true
```

**The actual synthesizer cascade (`src/orchestration/nodes/synthesizer.py`, lines 143–243):**
```
Tier 1: Cloud LLM (if CLOUD_SYNTHESIS_ALLOWED=true)
  ↓ if fails
Tier 2: Local LLM (llama.cpp or HuggingFace Phi-2)
  ↓ if fails
Tier 3: Rule-based formatting
```

**Issue 1:** The `LLM_FALLBACK_ORDER` env var is defined in `.env` but is **never read by the synthesizer**. The cascade order (cloud → local → rule-based) is hardcoded.

**Issue 2:** The `load_llm_settings()` function in `src/config/llm_config.py` only reads `LLM_PROVIDER` to determine which single provider to configure. The `fallback_order` list is stored in `LLMMeshConfig` but is never passed to or used by the synthesizer.

**Issue 3:** `CLOUD_SYNTHESIS_ALLOWED=true` is correctly enforced — cloud LLM is only called when this is `true`. Good.

**Impact:** The cascade works correctly for the configured path (NVIDIA → local → rule-based), but the `LLM_FALLBACK_ORDER` setting is decorative. If a user wanted `nvidia,gemini` fallback order, Gemini would never be tried because the synthesizer doesn't support multi-provider fallback.

**Recommendation:** Wire `LLM_FALLBACK_ORDER` into the synthesizer's `_synthesize()` function to dynamically iterate through providers in the specified order. Alternatively, document that the cascade is intentionally fixed as NVIDIA → local → rule-based.

### Local LLM Health Check: ✅ Robust

The `get_llama_cpp_client()` in `src/config/local_llm.py` (lines 245–269) has:
- 30-second health check cache to avoid repeated HTTP calls
- `ConnectError` → falls back to HuggingFace
- `TimeoutException` → raises, triggering next tier
- Cache expiry forces re-check on next request

This is well-designed for production use.

---

## 3. Auth/RBAC Tier Isolation Proof

### Finding: Tier Enforcement Is Partial — Middleware Not Wired to API

**Tier Model:**
| Tier | User | Access |
|------|------|--------|
| 1 | Researcher | Full access — names, emails, h-index, publications |
| 2 | Government | Aggregated stats only — no individual names |
| 3 | Industry | Names + research areas only — no personal details |

**Tier Enforcement Points:**

1. **Text-to-SQL (`src/skills/text_to_sql/skill.py`):** ✅ Tier filtering is applied via `WHERE tier_access <= user_tier` injected into all queries. This is the strongest enforcement point.

2. **Qdrant RBAC (`src/security/rbac/qdrant_rbac.py`):** ✅ `create_access_filter()` correctly builds a Qdrant filter restricting `access_tier` field. The `inject_access_filter()` method is present.

3. **API Middleware (`src/security/rbac/middleware.py`):** ⚠️ **NOT WIRED.** The `RBACMiddleware` class exists but is never applied to API endpoints. The `inject_postgresql_filter()` and `inject_qdrant_filter()` methods are stubs that just log — they don't actually modify queries.

4. **Synthesizer Tier Enforcement (`src/orchestration/nodes/synthesizer.py`):** ⚠️ **PARTIAL.** The `_format_researcher_table()` function (lines 494–528) shows email only for Tier 1:
   ```python
   if "email" in row and user_tier == 1 and row.get("email"):
       lines.append(f"      Email: {row['email']}")
   ```
   However, the `_minimise_sql_results()` function strips sensitive keys before sending to the LLM — this protects the LLM from seeing PII even if a bypass occurs. This is defense-in-depth.

5. **PostgreSQL RLS (`src/security/rbac/postgresql_rbac.py`):** ✅ RLS policies are defined in code. However, they are **never applied** — there is no call to `setup_rls_policies()` in the application startup. In SQLite mode (current), RLS is irrelevant. In PostgreSQL mode, this would need to be explicitly run.

### Critical Gap: Middleware Never Applied

The `RBACMiddleware` class is never instantiated in `src/api/main.py` or any route handler. This means:
- API endpoints could potentially return data above the user's tier if the SQL layer has a bug
- There is no API-layer filter catching tier violations before they reach the response

**Impact:** High. The SQL and Qdrant RBAC are the primary enforcement layers. If either has a bug, there is no API-layer backstop.

**Recommendation:**
1. Wire `RBACMiddleware` into all API endpoints that return research data
2. Add a tier check in the API response serialization layer
3. Run `PostgreSQLRBAC.setup_rls_policies()` during application startup when using PostgreSQL

---

## 4. Data Sovereignty Enforcement Audit

### Finding: ✅ Strong Sovereignty Posture

**Egress Guard (`src/security/egress/guard.py`):**

| Feature | Status | Notes |
|---------|--------|-------|
| Payload inspection | ✅ | Inspects all JSON payloads before cloud LLM calls |
| Sensitive field blocklist | ✅ | Blocks `full_text`, `abstract`, `raw_db_dump` etc. |
| Pattern detection | ✅ | Regex patterns for `publications.full_text`, `researchers.email` |
| Audit logging | ✅ | Sovereignty violations logged to audit chain |
| Configurable (NRG_SOVEREIGNTY_ENFORCED) | ✅ | Can be disabled for local-only mode |
| Bypass via header | ❌ | No `X-Bypass-Sovereignty` header — good |

**Synthesizer Data Minimization (`src/orchestration/nodes/synthesizer.py`):**

| Protection | Status | Notes |
|-----------|--------|-------|
| `_minimise_sql_results()` | ✅ | Strips sensitive keys (email, phone, etc.) before LLM call |
| `_minimise_chunks()` | ✅ | Only sends 700-char excerpts, not full documents |
| `_redact_text()` | ✅ | Regex-based PII redaction in results |
| Citation-only evidence | ✅ | Only `[cite:pub_id:chunk_id]` tokens reference source |
| Tier-based field filtering | ✅ | Email only shown to Tier 1 in `_format_researcher_table()` |

**PII Detection (`src/security/prompt_sanitiser.py`):**
Indian PII patterns are covered: Aadhaar, PAN, phone, email. The SovereigntyViolation exception properly halts execution on breach.

**Concern:** The egress guard is defined but **not actually used** in the LLM client calls. In `synthesizer.py`, `get_llm_client()` returns a raw HTTP client — it is NOT wrapped in `SovereignHTTPXClient`. The `_inspect_cloud_payload()` function exists but is only called in `load_llm_settings()` — not at request time.

**Impact:** Medium. The synthesizer passes data through `_minimise_sql_results()` and `_minimise_chunks()` before calling the LLM, which provides strong protection. But the formal egress guard mechanism is not actively intercepting cloud LLM calls.

**Recommendation:** Wrap the LLM client's HTTP calls with `SovereignHTTPXClient` or call `_inspect_cloud_payload()` on the request payload before every cloud LLM call. The infrastructure exists but isn't wired.

---

## 5. SQLite → PostgreSQL Migration Path

### Finding: Migration Infrastructure Exists, Not Yet Validated for Production

**Current State:**
- SQLite: ✅ Operational with 50K+ records
- PostgreSQL: ⚠️ Migrations exist but not deployed

**Alembic Migrations (`src/migrations/`):**
The `alembic.ini` exists and migrations are referenced. However, the actual migration files need verification.

**SQLAlchemy (`src/db/database_v2.py`):**
Dual-backend support — SQLite and PostgreSQL both supported via `create_engine()` with dialect detection.

**RLS Policies (`src/security/rbac/postgresql_rbac.py`):**
Defined but not automatically applied. Need to run `PostgreSQLRBAC.setup_rls_policies()` as part of migration.

**Migration Risk Assessment:**

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Data loss during migration | Low | High | Full SQLite backup before migration |
| RLS policies not applied | High | Medium | Add `setup_rls_policies()` to migration |
| Foreign key constraint failures | Medium | High | Disable FK checks during import, re-enable after |
| Downtime during migration | Medium | Medium | Use `pg_dump` live replication or maintenance window |
| Query performance regression | Low | Medium | Test queries on PostgreSQL before cutover |

**Recommendation:**
1. Add a pre-migration checklist to `docs/ops/dr_runbook.md`
2. Ensure `PostgreSQLRBAC.setup_rls_policies()` is called automatically on PostgreSQL connection
3. Validate all 40+ queries against PostgreSQL before cutting over from SQLite
4. Consider a blue/green deployment for the DB cutover

---

## Critical Findings (Ranked by Severity)

### 🔴 HIGH: RBAC Middleware Not Wired

**Severity:** High | **Component:** API Layer

The `RBACMiddleware` class exists but is never applied to any API endpoint. SQL-tier filtering is the only active enforcement layer. If a SQL injection bypass or query builder bug exists, there is no API-layer backstop.

**Fix:** Add `RBACMiddleware` to all research data endpoints in `src/api/main.py`.

---

### 🟡 MEDIUM: Reflector Node Not Implemented

**Severity:** Medium | **Component:** Orchestration

The Core_Idea_Clean.md describes a 6-node pipeline with a Reflector, but only 5 nodes are implemented. The pipeline still works, but self-evaluation and re-generation loops are missing.

**Fix:** Either implement Reflector node or update Core_Idea_Clean.md to reflect the actual 5-node architecture.

---

### 🟡 MEDIUM: `LLM_FALLBACK_ORDER` Ignored

**Severity:** Medium | **Component:** LLM Config

The `LLM_FALLBACK_ORDER=nvidia` env var is never read by the synthesizer. The cascade order is hardcoded as cloud → local → rule-based. The setting is decorative.

**Fix:** Read `LLM_FALLBACK_ORDER` in `_synthesize()` and iterate dynamically, or document that the cascade is fixed.

---

### 🟡 MEDIUM: Egress Guard Not Active on LLM Calls

**Severity:** Medium | **Component:** Security

`SovereignHTTPXClient` exists but is not wrapping the cloud LLM HTTP calls. Data minimization in the synthesizer provides equivalent protection, but the formal sovereignty boundary inspection is not active.

**Fix:** Wrap `get_llm_client()` HTTP calls with `SovereignHTTPXClient` or call `_inspect_cloud_payload()` on every request.

---

### 🟢 LOW: PostgreSQL RLS Policies Not Auto-Applied

**Severity:** Low | **Component:** Database

RLS policies are defined in `postgresql_rbac.py` but `setup_rls_policies()` is never called automatically. The policies exist in code but would not be active on a fresh PostgreSQL deployment.

**Fix:** Call `PostgreSQLRBAC(connection_string).setup_rls_policies()` during Alembic post-migrate hook or application startup.

---

## Recommendations Summary

| Priority | Action | Effort |
|----------|--------|--------|
| P0 | Wire RBACMiddleware into API endpoints | Medium |
| P0 | Add `setup_rls_policies()` to PostgreSQL startup | Low |
| P1 | Wire SovereignHTTPXClient into LLM client calls | Medium |
| P1 | Implement Reflector node or update Core_Idea_Clean.md | Medium |
| P2 | Validate LLM_FALLBACK_ORDER or remove from .env | Low |
| P2 | Full PostgreSQL migration dry-run in staging | High |

---

## Architecture Diagram (As-Built)

```
USER QUERY
    │
    ▼
┌──────────┐  session + ID    ┌──────────┐  sub-queries   ┌──────────┐  routing   ┌──────────┐  results
│ RECEIVER │─────────────────▶│ PLANNER  │────────────────▶│  ROUTER  │───────────▶│ EXECUTOR │
└──────────┘                 └──────────┘                 └──────────┘            └──────────┘
                                (fallback: None)             (heuristic)               │
                                                                                       ▼
                                                                              ┌─────────────────┐
                                                                              │ TEXT-TO-SQL (RBAC) │
                                                                              │ RAG (Qdrant RBAC) │
                                                                              └─────────────────┘
                                                                                       │
    ┌──────────────────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────┐  tier-filtered evidence    ┌──────────────┐
│ SYNTHESIZER  │───────────────────────────▶│   VERIFIER   │
└──────────────┘                              └──────────────┘
  1. Cloud LLM (if CLOUD_SYNTHESIS_ALLOWED)
  2. Local llama.cpp / Phi-2
  3. Rule-based formatter
  + _minimise_sql_results() / _minimise_chunks()
  + SovereignHTTPXClient (NOT WIRED ⚠️)
                                              ▼
                                             END
```

**Missing from diagram:** Reflector node (self-evaluation loop not implemented)