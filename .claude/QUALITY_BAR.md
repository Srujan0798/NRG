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

- **Protocol-level**: Every ═══ task's ACCEPTANCE CRITERIA must include any of the 6 constraints it touches.
- **CI-level**: Any test file under `tests/security/`, `tests/performance/`, `tests/load/` failing blocks merge.
- **Audit-level**: `/self-evolve` runs a "Quality Bar Compliance" check — scores each of the 6 on a 1–10 scale quarterly.
- **Guru-level**: Before marking any protocol COMPLETE in BACKLOG.md, the Guru verifies the 6 constraints are not violated by the change.

---

## Current Compliance Snapshot (2026-04-24)

| Constraint | Status | Owning Protocol |
|---|---|---|
| 1. DPDP Indian PII | ✓ Implemented, regression corpus exists | — |
| 2. Per-user audit binding | ✗ Missing | #35 (new) |
| 3. Multi-hop decomposition | ✗ Planner does flat decomposition | #37 (new) |
| 4. P99 <500ms / ≥1000 concurrent | ⚠ SLOs defined, numbers not these | #11 + #23 |
| 5. Vector drift + auto-retrain | ✓ Script exists, auto-trigger pending | #12 (tail) |
| 6. Schema allowlist before cloud | ✗ Fingerprint defense exists but not allowlist | #39 (new) |

**Score: 2 / 6 fully compliant.** Protocols #35, #37, #39 address the 3 missing constraints. Protocols #11/#23 tighten #4. Protocol #12 finishes #5.

---

## The Rule

> If any agent or Guru response claims "complete" on a task that touches any of the 6 constraints, verify compliance before accepting. A protocol is **not complete** if it regresses any of the 6 bars.
