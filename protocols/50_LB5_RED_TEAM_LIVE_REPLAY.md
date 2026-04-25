═══════════════════════════════════════════════════════════════
TASK: LB-5 — RED-TEAM LIVE REPLAY AGAINST RUNNING API
AGENT: security + testing
PRIORITY: P0-blocker
MILESTONE: M4 (Security Hardening)
QUALITY BAR: C6 (Schema allowlist before cloud LLM) + DPDP §43
RISK REGISTER: closes Risk #10
═══════════════════════════════════════════════════════════════

FILES:
  - scripts/red_team_live_replay.py (NEW)
  - tests/security/red_team_payloads.yaml (canonical 30 RT-01..RT-30 +
    extended ≥50)
  - evidence/2026-04-26/17_red_team_results.md (NEW, regenerated per session)

PROBLEM:
  Last red-team evidence used unit-level sanitiser tests (177/177) without
  live HTTP replay. We have no proof that the running uvicorn + middleware
  + RBAC + egress guard chain blocks all 30+ payloads end-to-end on real
  HTTP traffic.

ACTION:
  Phase 1 — FORTIFY:
    Implement red_team_live_replay.py: starts uvicorn (or assumes running),
    obtains tier-specific tokens, POSTs each payload to /query,
    /query/graph, /publications, /stats; classifies response as
    BLOCKED / DOWNGRADED / ALLOWED-DANGEROUS / ALLOWED-SAFE; writes
    timestamped Markdown evidence with payload hash + decision per call.

  Phase 2 — ELEVATE:
    Add new categories — bilingual injection (Hindi/English mixed),
    unicode-homoglyph PII, schema-name leakage probes, prompt-stealing
    attempts. Total payloads ≥ 50 across categories.

  Phase 3 — IMMORTALIZE:
    Nightly cron runs replay against staging API; any ALLOWED-DANGEROUS
    pages on-call + halts deploys until cleared. Audit-bind every
    classification entry to the per-user chain so we can prove the gate
    held during any post-incident review.

SKILLS TO USE:
  - /security-auditor — payload taxonomy, OWASP LLM Top 10 alignment
  - /python-backend — async HTTP fan-out, response classification
  - /testing-strategy — corpus design, regression gating
  - /code-review-and-quality

ACCEPTANCE CRITERIA:
  - [ ] All 30 baseline payloads → BLOCKED or DOWNGRADED on live API.
  - [ ] All ≥50 extended payloads classified, ZERO ALLOWED-DANGEROUS.
  - [ ] evidence/2026-04-26/17_red_team_results.md timestamped, signed in
        audit chain.
  - [ ] Quality Bar Constraint #6 score: 9+/10 with live evidence path.

BEFORE COMMIT:
  - /pre-commit + /code-review-and-quality + /security-auditor

GURU ASSIGNMENT NOTE:
  DPDP §43 imposes statutory liability per-incident. Sanitiser unit tests
  prove the function works in isolation. Live replay proves the WHOLE
  stack — middleware, RBAC, egress, audit, response-shape — refuses to
  leak under coordinated attack. Production launch cannot proceed without
  this evidence file.

AGENT INSTRUCTIONS (verbatim):
  - Standard agent reads (production_only, AGENTS, shishya, QUALITY_BAR).
  - Read .claude/NRG_CONSTITUTION.md §1.
  - Read docs/runbooks/PRODUCTION_LAUNCH_RISK_REGISTER.md Risk #10.
  - Read every SKILL.md listed.
  - Fortify → Elevate → Immortalize.
  - /pre-commit + /code-review-and-quality + /security-auditor before commit.

DEPENDS ON: LB-1 (#46) — tier-shape filter must be live first
BLOCKS: production launch
═══════════════════════════════════════════════════════════════
