═══════════════════════════════════════════════════════════════
TASK: #27 — THE FINAL GREEN (v2, updated 2026-04-24 post-Phase-5)
AGENT: backend / testing / security
PRIORITY: P0-blocker
═══════════════════════════════════════════════════════════════

CURRENT TEST STATE (baseline):
  1135 passed · 15 failed · 58 skipped · 20 errors · 1228 collected
  Target: 1228 / 0 failed / 0 errors (skipped ok if justified)

FILES:
  - src/audit/__init__.py (missing datetime import — 4 failures + 20 errors)
  - src/audit/per_user_keys.py (consent event labeling regression)
  - src/orchestration/nodes/planner.py (comparison query DAG — 1 branch, should be 2)
  - src/orchestration/nodes/synthesizer.py (provenance field missing)
  - src/orchestration/nodes/router.py (minimax primary provider edge)
  - src/auth/rbac.py (window_to_only filter edge case)
  - Test files under tests/security/, tests/e2e/, tests/orchestration/

PROBLEM CATEGORIES:

A. DATETIME NAMEERROR CASCADE (4 failures + 20 errors)
   - tests/security/test_audit_chain.py::test_verify_fails_tampered
   - tests/security/test_audit_chain.py::test_verify_fails_deleted_event
   - tests/security/test_security_regression.py::test_tampered_chain_fails_verification
   - tests/security/test_security_regression.py::test_user_key_hash_computed
   - Plus 20 errors likely cascaded from same root cause
   - Root cause: missing `from datetime import datetime` or similar in src/audit/

B. CONSENT AUDIT EVENT LABELING REGRESSION (3 failures)
   - test_grant_writes_audit_event: expected 'consent_granted', got 'sql'
   - test_revoke_writes_audit_event: expected 'consent_revoked', got 'anomaly_detected'
   - test_erasure_writes_audit_event: expected 'data_erasure', got 'anomaly_detected'
   - Root cause: #35 per-user binding change broke consent event type assignment

C. SYNTHESIZER PROVENANCE FIELD (3 failures)
   - test_every_response_has_synthesis_method: provenance must have 'synth' field
   - test_cloud_llm_flag_reflects_actual_provider: cloud_synthesis_used must be False for local/rule-based
   - test_all_tiers_receive_correct_synthesis_method: researcher must have provenance
   - Root cause: synthesizer not populating provenance consistently across paths

D. MULTI-HOP DAG PARALLEL BRANCHES (1 failure)
   - test_comparison_query_parallel_branches: assert 1 >= 2
   - Root cause: #37 planner generates 1 DAG branch for comparison queries when it should generate 2

E. WORKFLOW PIPELINE (2 failures)
   - test_workflow_runs_full_orchestration_pipeline: assert 0 == 1
   - test_workflow_surfaces_rag_failures_as_warnings: warnings list empty
   - Root cause: pipeline integration regressions from Phase 5 changes

F. ROUTER MINIMAX EDGE (1 failure)
   - test_minimax_is_primary_provider: sql_only instead of cloud_llm/fallback
   - Root cause: router 2-stage keyword match triggers sql_only incorrectly

G. TEMPORAL RBAC WINDOW EDGE (1 failure)
   - test_window_to_only: assert False is True
   - Root cause: #36 window filter doesn't correctly handle window with only 'to' bound (no 'from')

ACTION:
  Phase 1 — FORTIFY: Fix the datetime cascade (quickest, unblocks 20 errors)
    1a. Grep src/audit/ for datetime usage without import. Add `from datetime import datetime, timezone`.
    1b. Re-run only tests/security/test_audit_chain.py + test_security_regression.py — should go from
        4 failed + many errors to 0 failed.
  
  Phase 2 — FORTIFY: Fix Phase 5 regressions (Categories B, D, G)
    2a. B: Consent event labels. In src/audit/__init__.py or per_user_keys.py, find where event_type
        is set. Ensure 'consent_granted', 'consent_revoked', 'data_erasure' are NOT overwritten by
        anomaly detection or default routing.
    2b. D: In src/orchestration/nodes/planner.py _build_dag(), ensure comparison queries
        (detect via "compare", "vs", "versus" keywords or LLM output hint) produce ≥2 parallel
        branches. Update the LLM prompt's few-shot examples if needed.
    2c. G: In src/auth/rbac.py is_within_window(), handle case where 'from' is None (only 'to' bound).
        Logic: if only 'to' is set, any row with timestamp ≤ to is in window.
  
  Phase 3 — FORTIFY: Fix synthesizer + router + pipeline (Categories C, E, F)
    3a. C: In src/orchestration/nodes/synthesizer.py, ensure every return path writes:
        response["provenance"] = {"synth": synthesis_method, "cloud_synthesis_used": bool}
        All 3 paths: cloud LLM, local SLM, rule-based.
    3b. E: Run test_workflow_runs_full_orchestration_pipeline with -v to see where the assertion
        actually fails. Fix the regression (likely state handoff between nodes).
    3c. F: Router's keyword-match stage — check fixture in test_minimax_is_primary_provider.
        If query contains "minimax" literally, the 2-stage router matches "min" keyword.
        Refine keyword list or add NOT-patterns.
  
  Phase 4 — IMMORTALIZE: Verification gate
    4a. Run full test suite: target 1228 passed / 0 failed / 0 errors.
    4b. Run Dhairya benchmark: `python scripts/benchmark_dhairya_queries.py`. Report accuracy.
    4c. Verify Quality Bar constraints not regressed:
        - #2 Non-repudiation: verify_chain still returns valid per-user signatures
        - #3 Multi-hop: comparison queries now produce ≥2 branches
        - #6 Egress: /security/test_egress_allowlist.py still green
    4d. Commit with message: "fix: #27 Final Green — all tests passing, Phase 3 closed"

SKILLS TO USE:
  - /bug-hunt — Root cause for the 15 specific failures + 20 errors (NO symptom-patching)
  - /test-suite — Track delta after each category fix
  - /python-backend — Fix imports, state handling, pipeline integration
  - /security-auditor — Verify #35 per-user binding still valid after consent fix
  - /code-review-and-quality — Self-review before submitting

ACCEPTANCE CRITERIA:
  - [ ] All 15 failures resolved
  - [ ] All 20 errors resolved
  - [ ] Test suite: 1228 passed / 0 failed / ≤58 skipped
  - [ ] Dhairya benchmark runs end-to-end, accuracy % recorded
  - [ ] Quality Bar compliance NOT regressed (6 constraints all still green)
  - [ ] No new failures introduced (regression check)
  - [ ] `verify_chain()` still valid with per-user binding

BEFORE COMMIT:
  - Run /pre-commit — must pass all gates
  - Run /code-review-and-quality on your changes
  - Run /security-auditor on the audit chain changes
  - Report test count: target 1228/0 (or better)

GURU ASSIGNMENT NOTE:
  Phase 5 Quality Bar landed — all 6 constraints implemented in code. But landing code created
  15 failing tests + 20 errors: some are legit Phase 5 bugs, some are pre-existing that were
  masked. This is the LAST protocol before Protocol #28 Eternal Completion. Green here means
  NRG is ready for client handover. The datetime cascade is trivial (20 errors from 1 missing
  import). The consent regression is a real Phase 5 bug. The multi-hop branch bug is a real
  Phase 5 limitation. Close all three cleanly and the 40-crore project stands ready for the
  professor at IIT Gandhinagar.

AGENT INSTRUCTIONS (verbatim):
  - Read .agents/AGENTS.md, shishya_universal.md
  - Read every SKILL.md listed above
  - Read Core_Idea_Clean.md, BACKLOG.md
  - Read .claude/QUALITY_BAR.md — verify no Quality Bar regression
  - Check .claude/CLAUDE.md "THE 3 DATA SOURCES"
  - Fortify → Elevate → Immortalize
  - /pre-commit before committing
  - Report per .agents/AGENTS.md format, include Quality Bar compliance check

DEPENDS ON: Phase 5 code (committed f64ed1b6)
BLOCKS: #28 Eternal Completion
═══════════════════════════════════════════════════════════════
