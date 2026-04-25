═══════════════════════════════════════════════════════════════
TASK: LB-1 — TIER-SHAPE FILTER AT API RESPONSE BOUNDARY
AGENT: backend + security
PRIORITY: P0-blocker (production launch + DPDP §8(4))
MILESTONE: M3 (Authentication) + M4 (Security Hardening)
QUALITY BAR: C2 (Per-User Audit Binding non-repudiation)
RISK REGISTER: closes Risk #2, #13
═══════════════════════════════════════════════════════════════

FILES:
  - src/api/main.py — every JSONResponse path: /query, /query/graph,
                      /publications, /stats, /api/query/stream
  - src/api/middleware/security.py — tier enforcement check
  - src/auth/rbac.py — `tier_response_columns` allowlist (NEW or extend)
  - rbac_policies.yaml — single source of column → tier mapping
  - tests/api/test_tier_isolation_live.py (NEW)
  - tests/api/test_tier_isolation_property.py (NEW — hypothesis)
  - evidence/2026-04-26/09_tier1_query_response.json (NEW)
  - evidence/2026-04-26/10_tier2_query_response.json (NEW)
  - evidence/2026-04-26/11_tier3_query_response.json (NEW)
  - .claude/memory/feedback_tier_shape_boundary.md (read for rationale)

PROBLEM:
  Earlier evidence JSONs (09/10/11_tierN) showed materially identical
  structures across tiers. RBAC column stripping is enforced at the SQL
  layer but NOT proven at the API response-shape layer. Risk: synthesizer/
  verifier nodes touch raw rows in memory — any future code path that
  composes results across tables, returns cached rows, or renders a graph
  could leak email/phone/Aadhaar to Tier 3. One leaked PII column = DPDP
  §8(4) statutory violation = end of IIT-GN engagement.

ACTION:
  Phase 1 — FORTIFY:
    1a. Add `_apply_tier_response_filter(payload, tier)` invoked immediately
        before every `JSONResponse(...)` in src/api/main.py. Strips: email,
        phone, aadhaar, pan, dob, full_address, bank_account, gstin from any
        row in response.sql_results, response.citations,
        response.retrieval_sources for tier ≥ 2. For tier 3, also replace
        personal_name with `Researcher_<id>`.
    1b. Allowlist sourced from rbac_policies.yaml `tier_response_columns`,
        not hardcoded per endpoint.
    1c. Same filter applied to /api/query/stream (SSE chunks) and
        /query/graph (node + edge labels).

  Phase 2 — ELEVATE:
    2a. Response-shape contract test: schema diff per tier must show ≥4
        columns differ between T1 and T3. Auto-generated from
        rbac_policies.yaml; fails CI if a column is added without explicit
        tier classification.
    2b. Audit-log every strip event with reason `pii_strip:tier3:email`
        bound to per-user audit chain — proves later that no PII reached T3
        even on payloads that originally contained it.

  Phase 3 — IMMORTALIZE:
    3a. Property-based test (hypothesis): generate 1000 random sql_results
        with random PII column mixes; for every tier ∈ {1,2,3} the post-shape
        payload contains zero disallowed columns. Run nightly + on every PR
        touching api/main.py or rbac.
    3b. Add /api/internal/tier_diff (Tier 1 only) returning live diff of
        last 100 responses per tier — operator spot-check for sovereignty.
        Gated by RBAC + audit-logged on every access.

SKILLS TO USE:
  - /security-auditor — RBAC pattern review, DPDP alignment, PII taxonomy
  - /python-backend — FastAPI response shaping, dependency injection
  - /testing-strategy — property-based, contract, evidence-capture
  - /code-review-and-quality — mandatory self-review

ACCEPTANCE CRITERIA:
  - [ ] tests/api/test_tier_isolation_live.py: T1, T2, T3 receive measurably
        different responses for the same query (≥4 columns differ T1↔T3).
  - [ ] tests/api/test_tier_isolation_property.py: 1000 hypothesis cases ×
        3 tiers → 0 PII leaks.
  - [ ] evidence/2026-04-26/09–11_tierN_query_response.json regenerated
        against running uvicorn with curl + Bearer token per tier.
  - [ ] Audit chain shows pii_strip:* events bound to per-user chain.
  - [ ] Quality Bar Constraint #2 NOT regressed (verify_chain still valid).
  - [ ] Cost impact: 0 (filter operates on already-fetched payload).

BEFORE COMMIT:
  - /pre-commit (forbidden-vocab + check-env + gitleaks must pass)
  - /code-review-and-quality on every touched file
  - /security-auditor on src/api/main.py response paths
  - Forbidden vocabulary check: scripts/forbidden_vocab_check.sh must exit
    0 against every new file, comment, and commit message. The script is
    the source of truth for the rejected token list (see
    .claude/rules/production_only.md).

GURU ASSIGNMENT NOTE:
  This is the single highest-impact gap before the IIT-GN user acceptance
  session. The first credibility test will not be "is the SQL right?" — it
  will be "if I log in as Tier 3, do I see what Tier 3 should see?". One
  leaked researcher email and the engagement ends the same minute. Make the
  filter unbypassable so even a future careless `return jsonify(rows)`
  cannot defeat it. Two layers of defence: SQL boundary + response boundary.

AGENT INSTRUCTIONS (verbatim):
  - Read .agents/AGENTS.md, .agents/prompts/shishya_universal.md
  - Read .claude/rules/production_only.md FIRST
  - Read .claude/QUALITY_BAR.md (C2 + Tier-Shape Boundary + Live Evidence)
  - Read .claude/NRG_CONSTITUTION.md §1
  - Read .claude/memory/feedback_tier_shape_boundary.md
  - Read every SKILL.md listed above
  - Read docs/runbooks/PRODUCTION_LAUNCH_RISK_REGISTER.md Risk #2 + #13
  - Fortify → Elevate → Immortalize
  - /pre-commit + /code-review-and-quality + /security-auditor before commit
  - Report which skills you used and what you elevated beyond minimum

DEPENDS ON: none
BLOCKS: production launch
═══════════════════════════════════════════════════════════════
