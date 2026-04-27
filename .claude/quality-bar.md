# NRG QUALITY BAR — The 6 Hard Constraints

> Every protocol, every task, every agent output must satisfy these. Not aspirational — **acceptance-blocking**. If a deliverable violates any of the 6, it is not complete regardless of what the BACKLOG or the agent claims.

Source: Encoded into the workflow on 2026-04-24 from an external validator prompt. Re-validated against `Core_Idea_Clean.md` and measured current state.

---

## The 6 Constraints

### 1. DPDP-Compliant Indian PII Detection
**Must detect and block**: PAN (`[A-Z]{5}[0-9]{4}[A-Z]`), Aadhaar (12-digit with Verhoeff checksum), Indian mobile (`+91|0?[6-9]\d{9}`), email, passport, GSTIN, bank account.
**Where enforced**: `src/security/pii/` — regression test `tests/security/test_pii_indian.py` must cover all 7 patterns with positive + adversarial cases.
**Acceptance test**: zero false negatives on the Indian PII corpus.

### 2. Per-User Audit Binding (Non-Repudiation)
**Must attach**: every audit event carries `user_id`, `persona`, `jwt_jti`, `request_fingerprint`, HMAC signed with a per-user derived key.
**Why**: current HMAC chain is tamper-proof at the chain level but an attacker who steals a JWT can impersonate a user. Per-user binding + multi-party attestation closes this.
**Where enforced**: `src/audit/__init__.py` — `AuditLogger.log_event()` must reject events without per-user binding.
**Acceptance test**: `verify_chain()` returns `False` if any event's per-user signature fails.

### 3. Multi-Hop Intent Decomposition
**Must support**: questions that require 2+ sub-queries with dependencies. Example: "Compare Gujarat and Karnataka's AI research output over 5 years and show the funding gap."
**Where enforced**: `src/orchestration/nodes/planner.py` — output `sub_queries` must be a DAG (dependency graph), not a flat list.
**Acceptance test**: `tests/orchestration/test_multi_hop_planner.py` with 10 multi-hop fixtures, all decomposed correctly.

### 4. Production SLOs
**Must meet**: P99 latency < 500ms for analytical queries, ≥1000 concurrent users without degradation.
**Where enforced**: `tests/performance/test_slo_compliance.py`, `tests/load/test_slo_under_load.py`.
**Acceptance test**: SLO tests run in CI and block merge on breach. SLO breach detection in `src/observability/metrics.py` logs CRITICAL on 5 consecutive breaches.

### 5. Vector Drift Monitoring + Auto-Retrain Trigger
**Must detect**: embedding drift cosine shift > 0.05 against reference vectors. When triggered, emit event to re-index queue.
**Where enforced**: `scripts/vector_drift_check.py` runs weekly (cron or CI). Emits to `src/observability/metrics.py`.
**Acceptance test**: manual drift simulation triggers retrain event within 1 minute.

### 6. Schema Allowlist Before Cloud LLM Exposure
**Must enforce**: egress guard inspects every outbound LLM payload. Only allowlisted schema fragments may appear. Raw DB schema, column names not in the allowlist, sensitive metadata — blocked.
**Where enforced**: `src/security/egress_guard/` — new allowlist config at `src/security/egress_allowlist.yaml`.
**Acceptance test**: `tests/security/test_egress_allowlist.py` with 20+ attempts to leak non-allowlisted schema, all blocked.

---

## Enforcement

- **Scorecard**: `python scripts/quality_bar_scorecard.py` — runs all 6 test groups, emits markdown + JSON to `scripts/quality_bar_scorecard.json`. Exit code 1 if not 6/6.
- **CI-level**: `.github/workflows/cd.yml` — `quality-bar` job runs scorecard before build; blocks all deployments (build, staging, production) unless scorecard reports 6/6.
- **Nightly**: Scorecard runs as a cron job; any score drop triggers a P0 incident alert.
- **Protocol-level**: Every task's ACCEPTANCE CRITERIA must include any of the 6 constraints it touches.
- **Quarterly**: `/self-evolve` runs scorecard; result committed to `docs/ops/QUALITY_BAR_SCORECARD_<YYYY-QN>.md`.
- **Guru-level**: Before marking any protocol COMPLETE in BACKLOG.md, the Guru verifies the 6 constraints are not violated by the change.

---

## Current Compliance Snapshot (2026-04-26)

| Constraint | Status | Owning Protocol | Notes |
|---|---|---|---|
| 1. DPDP Indian PII | ✓ Implemented, 8/8 tests passing | — | PAN, Aadhaar, mobile, email, passport, GSTIN, bank account |
| 2. Per-user audit binding | ✓ 26/26 tests passing | #35 | verify_chain() rejects tampered bindings |
| 3. Multi-hop decomposition | ✓ 24/24 tests passing | #37 | 10+ multi-hop fixtures, DAG planner |
| 4. P99 <500ms / ≥1000 concurrent | ⚠ Unit tests pass (10/12); load test needs API+Qdrant | #11 + #23 | `tests/load/locustfile.py` — requires live system |
| 5. Vector drift + auto-retrain | ⚠ Script runs; Qdrant required for full validation | #12 (tail) | `scripts/vector_drift_check.py` — requires Qdrant on 6333 |
| 6. Schema allowlist before cloud | ✓ 35/35 tests passing | #39 | All 20+ egress leak attempts blocked |

**Score: 5/6 fully passing in dev. 2/6 require infrastructure (C4: API+Qdrant, C5: Qdrant).**

**Scorecard script**: `python scripts/quality_bar_scorecard.py` — runs all 6 test groups, emits markdown + JSON.
**CI enforcement**: `.github/workflows/cd.yml` — `quality-bar` job blocks all deployments unless scorecard is 6/6.

---

## The Rule

> If any agent or Guru response claims "complete" on a task that touches any of the 6 constraints, verify compliance before accepting. A protocol is **not complete** if it regresses any of the 6 bars.

---

## Live Evidence Requirement (added 2026-04-26)

A unit-test pass alone never satisfies any constraint above. For every claim of "PASS", the evidence must include **at least one of**:

1. A captured response from a **running uvicorn API + populated Qdrant + ≥50k-row staging PostgreSQL**, committed under `evidence/<YYYY-MM-DD>/` as JSON or Markdown.
2. A scorecard run by `scripts/quality_bar_scorecard.py` against that running stack — the JSON output is the source of truth.
3. A signed audit-chain entry in `.audit/chain.jsonl` referencing the same artifact.

> **Tests on 10-row seed data are deferred bugs, not passing tests.** Every Quality Bar PASS must be reproducible against a running system at production-realistic volume — see `.claude/rules/audit/protocol.md` "Real Volume Reality Check".

---

## Tier-Shape Boundary (added 2026-04-26)

RBAC enforcement must happen at **two** layers, not one:

| Layer | Mechanism | Failure mode if missing |
|---|---|---|
| SQL boundary | `tier_query_filters` in `rbac_policies.yaml` strips columns from SELECT | Researcher email never enters the executor result |
| **Response-shape boundary** | Last-mile filter in `src/api/main.py` re-applies the tier allowlist before `JSONResponse` | Synthesizer can never accidentally render a column the SQL boundary missed |

Constraint #2 (Per-User Audit Binding) is regressed if any /query, /query/graph, /publications, /stats, or /api/query/stream response delivers a column not in the requesting user's tier allowlist — even if the SQL filter blocked it. Property-test with hypothesis to prove no PII leaks across 1000 random payloads × 3 tiers.

---

## Verdict Template (binding for every audit-style response)

Any audit-style report (Guru, agent, or external reviewer) must end with this exact block:

```
OVERALL READINESS: <X.Y / 10>
LAUNCH-READY:      <YES / NO> — if NO, three items that must close first
PRODUCTION-READY:  <YES / NO> — if NO, three items that must close first
BIGGEST SINGLE RISK: <one sentence, traced to file:line or evidence file>
WHAT WILL IMPRESS THE USER:    <one sentence>
WHAT WILL EMBARRASS THE TEAM:  <one sentence>
```

This is the only acceptance template. Free-form scoring is rejected.
