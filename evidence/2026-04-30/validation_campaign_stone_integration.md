# Validation Campaign Stone Integration - 2026-04-30

Restored on 2026-05-01 because `.claude/CURRENT_STATE.md` and
`evidence/2026-04-30/FINAL_EVIDENCE_INDEX.md` referenced this file after it was
removed by a later cleanup pass. The content below preserves the original
integration note and makes the evidence link valid again.

## Scope

Integrated the useful strategy from an external broad-validation prompt into the
NRG hybrid prompt system without converting NRG into a generic application or
copying impossible claims.

## New Stone

- `prompts_hybrid/08_full_coverage_validation_campaign_stone.md`

## Workflow Entry Points

- `.agents/skills/nrg-validation-campaign/SKILL.md`
- `.claude/skills/nrg-validation-campaign/SKILL.md`
- `.claude/CLAUDE.md` Product Quality skill inventory and task routing table

## What Was Kept

- Broad query corpus strategy.
- Tier comparison across Researcher, Government, and Industry.
- Complete workflow validation.
- UI interaction and state coverage.
- Security, PII, prompt-injection, tier-escalation, and small-cohort probes.
- Audit/event proof requirements.
- Evidence indexing and step logging.
- Self-audit/finding/fix/retest loop.
- Local-vs-cluster performance distinction.

## What Was Removed Or Normalized

- Artificial hour requirements.
- Impossible completion claims.
- Arbitrary massive step counts as proof by themselves.
- Requiring screenshots for every single API-level query.
- Standalone `index.html` demands that conflict with NRG's existing
  React/Vite/FastAPI architecture.
- Generic application framing that does not fit NRG's sovereign research
  answer-engine workflow.

## NRG-Specific Upgrade

The new stone uses campaign modes:

- `calibration`
- `acceptance`
- `release-candidate`
- `cluster-proof`

It requires a declared coverage matrix instead of vague "everything" claims.
It also enforces the current C4 truth:

- local 100-user C4 smoke passed in
  `evidence/2026-04-30/live_c4_local_smoke_after_read_model_final/`
- production readiness still needs 1000-user sovereign-cluster/deployed proof

## Files Updated

- `prompts_hybrid/00_INDEX.md`
- `prompts_hybrid/01_master_execution_stone.md`
- `prompts_hybrid/06_evidence_acceptance_stone.md`
- `prompts_hybrid/07_show_readiness_handover_stone.md`
- `prompts_hybrid/ARCHIVE_NOTES.md`
- `.agents/skills/nrg-validation-campaign/SKILL.md`
- `.claude/skills/nrg-validation-campaign/SKILL.md`
- `.claude/CLAUDE.md`
- `.claude/CURRENT_STATE.md`

## Verification Recorded In Original Integration Pass

Command:

```bash
git diff --check -- prompts_hybrid .claude/CURRENT_STATE.md evidence/2026-04-30/validation_campaign_stone_integration.md
```

Result: passed with no whitespace errors.

Unsafe external-framing scan across active prompt stones:

Result: no unsafe copied external-prompt framing remained in active prompt
stones.
