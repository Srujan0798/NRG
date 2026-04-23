═══════════════════════════════════════════════════════════════
TASK: #39 — THE SCHEMA ALLOWLIST
AGENT: backend / security
PRIORITY: P0-blocker (Quality Bar Constraint #6)
═══════════════════════════════════════════════════════════════

FILES:
  - src/security/egress_guard/ (extend existing)
  - src/security/egress_allowlist.yaml (NEW — declarative allowlist)
  - src/orchestration/nodes/synthesizer.py (invoke egress guard before every cloud LLM call)
  - src/config/llm_config.py (add egress check before provider.generate)
  - tests/security/test_egress_allowlist.py (NEW — 20+ leak attempts)
  - .claude/QUALITY_BAR.md (Constraint #6 reference)

PROBLEM:
  Current egress guard inspects payloads but doesn't enforce a STRICT allowlist of what schema
  fragments may appear in outbound LLM calls. Schema fingerprint defense exists (stops probing
  attacks) but doesn't prevent our own system from accidentally leaking table/column names.
  
  Security axiom from Core_Idea_Clean.md: "Cloud LLMs receive only the user question + retrieved
  facts for synthesis — never raw database, schemas, PII, or unrestricted data dumps."
  
  Current gap: if synthesizer includes `"found in researchers_patents_details table"` in a
  prompt, that metadata leaks. Need explicit allowlist of which schema fragments are ok.

ACTION:
  Phase 1 — FORTIFY: Allowlist YAML + loader
    1a. Create src/security/egress_allowlist.yaml with schema:
        ```yaml
        allowed_schema_fragments:
          tables:
            - publications  # ok to reference in cloud prompts
            - researchers
          columns:
            - researchers.research_area
            - publications.title
          patterns:
            - "^publication_id: PUB_\\d+$"
        blocked_schema_fragments:
          tables:
            - audit_events  # never leak system tables
            - consent_ledger
            - refresh_tokens
            - training_pairs
          columns:
            - researchers.email
            - researchers.phone
            - researchers.aadhaar
          patterns:
            - "^INSERT INTO|^UPDATE |^DELETE FROM"  # no DDL leaks
        ```
    1b. Loader validates YAML schema, caches parsed rules, supports hot-reload on file change.
  
  Phase 2 — ELEVATE: Egress guard enforcement
    2a. Extend src/security/egress_guard/ with `inspect_payload(payload) -> EgressDecision`.
        Decision types: ALLOW, BLOCK (with reason), WARN (logged, not blocked).
    2b. Scan payload for: blocked table names, blocked column names, PII patterns,
        SQL DDL statements, non-allowlisted schema fragments that look like schema.
    2c. Wire into src/config/llm_config.py BEFORE every provider call. If BLOCK — raise
        EgressViolation, log to audit chain, return error to user: "Response blocked by
        data sovereignty rules."
    2d. Audit log every BLOCK with: rule matched, payload hash, user_id, timestamp. Never log
        the full blocked payload (that itself could leak).
  
  Phase 3 — IMMORTALIZE: Adversarial test corpus
    3a. tests/security/test_egress_allowlist.py with 20+ attack scenarios:
        - Prompt contains blocked table name directly → BLOCK
        - Prompt contains blocked column → BLOCK
        - Prompt contains SQL DDL → BLOCK
        - Prompt contains PII (Aadhaar, PAN, phone) → BLOCK
        - Prompt contains allowed table + data → ALLOW
        - Prompt contains schema via obfuscation (e.g., "the auditing log") → WARN
        - Multi-table join description with one blocked table → BLOCK
        - Empty payload → ALLOW
        - Payload with allowed metadata only → ALLOW
    3b. Add scripts/egress_audit.py — scans recent LLM calls (from observability), reports
        any payload that contained blocked patterns but was NOT blocked (gap detector).
    3c. Add to /pre-commit: if src/security/egress_allowlist.yaml changed, run adversarial
        test suite. Block commit if any ALLOW is granted to a known-bad pattern.

SKILLS TO USE:
  - /security-auditor — Egress DLP patterns, adversarial test design, YAML config design
  - /python-backend — YAML loading, hot-reload, LRU caching
  - /prompt-engineering-patterns — What leaks in typical LLM prompts, mitigation patterns
  - /testing-strategy — Adversarial corpus design, regression gating
  - /code-review-and-quality — Self-review

ACCEPTANCE CRITERIA:
  - [ ] src/security/egress_allowlist.yaml exists, documented, loaded at startup
  - [ ] egress_guard.inspect_payload() returns typed EgressDecision
  - [ ] ALL cloud LLM calls pass through egress guard (grep-verified, zero bypass)
  - [ ] Blocked calls raise EgressViolation + audit log entry
  - [ ] tests/security/test_egress_allowlist.py — 20+ scenarios, all passing
  - [ ] scripts/egress_audit.py runs without detecting leak-gaps on sample data
  - [ ] /pre-commit gates egress allowlist changes
  - [ ] Quality Bar Constraint #6 compliance score: 8+/10

BEFORE COMMIT:
  - Run /pre-commit
  - Run /security-auditor on the changes
  - Verify no existing tests regress (the egress check must not break working flows)
  - Run scripts/egress_audit.py on last 1000 LLM calls — zero gaps

GURU ASSIGNMENT NOTE:
  The #1 sovereignty axiom — "the 600GB never leaves Indian servers" — depends on this.
  Raw data already stays local (enforced by architecture). But metadata about the data —
  table names, column names, schema structure — leaks via cloud LLM prompts every time
  synthesizer includes context. An attacker reading cloud LLM logs could reverse-engineer
  the NRG schema without ever touching our DB. This protocol enforces: only what we
  EXPLICITLY allowlist leaves. Everything else gets blocked and audited. DPDP 2023's
  "purpose limitation" is not just about raw data — it's about metadata too.

AGENT INSTRUCTIONS (verbatim):
  - Read .agents/AGENTS.md, shishya_universal.md
  - Read every SKILL.md listed
  - Read .claude/QUALITY_BAR.md — this closes Constraint #6
  - Read .claude/NRG_CONSTITUTION.md §1 (Zero-Leakage Rules)
  - Read Core_Idea_Clean.md §"Security Model" — understand what never leaves
  - Fortify → Elevate → Immortalize
  - /pre-commit + /security-auditor before committing

DEPENDS ON: none (independent of test baseline)
═══════════════════════════════════════════════════════════════
