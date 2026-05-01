# Central Execution Flow Map Evidence

Date: 2026-05-02

## Scope

Created the central NRG operating map:

- `docs/specs/NRG_EXECUTION_FLOW_RULE_HIERARCHY_2026-05-02.md`

Linked it from:

- `docs/specs/NRG_SOURCE_OF_TRUTH_MAP_2026-04-30.md`
- `.claude/CURRENT_STATE.md`
- `BACKLOG.md`
- `.claude/memory/INDEX.md`

## Source Files Read

- `.claude/rules/production_only.md`
- `.claude/CURRENT_STATE.md`
- `docs/specs/NRG_SOURCE_OF_TRUTH_MAP_2026-04-30.md`
- `.claude/memory/INDEX.md`
- `.claude/protocol.md`
- `.claude/quality-bar.md`
- `.claude/agent-warfare.md`
- `.claude/constitution.md`
- `.claude/rules/audit/index.md`
- `.claude/rules/ux/index.md`
- `.claude/skills/nrg-validation-campaign/SKILL.md`
- `.claude/skills/pre-commit/SKILL.md`
- `prompts_hybrid/06_evidence_acceptance_stone.md`
- `prompts_hybrid/08_full_coverage_validation_campaign_stone.md`
- `NRG_FINAL_ETERNAL_AUDIT_2026-04-27.md`
- `BACKLOG.md`
- `evidence/2026-05-02/guru_shishya_validation/c4_rerun/README.md`
- `evidence/2026-05-02/guru_shishya_validation/c4_rerun/74_query_stage_profile_summary_after_critical_section.md`
- `evidence/2026-05-02/guru_shishya_validation/c4_rerun/75_rate_limit_and_quota_mode_boundary.md`

## C4 Interpretation

C4 is Quality Bar Constraint 4: production SLOs. It requires at least 1000
concurrent users, zero request failures, and P99 latency below 500 ms.

Current status remains **FAIL**. Latest useful evidence shows 45,559 samples and
zero failures, but aggregate P99 is 2100 ms after declared workload prewarm.

## Verification

Passed:

- `git diff --check` exited 0.
- `python3 scripts/verify_corpus_sync.py` returned `"ok": true`; all canonical
  corpus mirrors matched.
- `bash scripts/forbidden_vocab_check.sh --all` exited 0.
