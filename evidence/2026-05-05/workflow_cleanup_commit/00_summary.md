# Workflow Cleanup Commit

## What Changed
- Committed 17 files: deploy gate stone, remote workflow, evidence diet, verification scripts, memory archive
- Commit SHA: `2c0a6a00`

## Files Added
- `prompts_hybrid/09_deployment_gate_stone.md`
- `.claude/REMOTE_WORKFLOW.md`
- `scripts/nrg-remote-setup.sh`
- `.devcontainer/devcontainer.json`
- `.claude/scripts/nrg-verify-workflow.py`
- `.claude/scripts/nrg-skill-count.py`
- `.claude/scripts/nrg-evidence-prune.py`

## Files Modified
- `prompts_hybrid/07_show_readiness_handover_stone.md` (mandates staging URL)
- `prompts_hybrid/06_evidence_acceptance_stone.md` (5 artifacts per task)
- `.claude/CURRENT_STATE.md` (simplified to 80 lines)
- `.claude/CLAUDE.md` (forbidden vocab purge)
- `.claude/MANIFEST.md` (corrected skill counts)
- `AGENTS.md`, `.agents/AGENTS.md`
- `docs/specs/CLOSURE_PLAN_2026-04-26.md`
- `prompts_hybrid/00_INDEX.md`
- `.claude/memory/references/INDEX.md`

## Files Deleted
- `.agents/skills/nrg-validation-campaign/SKILL.md` (duplicate)
- `.claude/memory/references/grok-principal-engineer-2026-04-25.md`
- `.claude/memory/references/principal-auditor-2026-04-26.md`
- `.claude/memory/sprint_retrospective_2026-04-27.md`

## Verification
- `nrg-verify-workflow.py`: ALL CHECKS PASSED

## Blocker
- Push to `nrg/main` BLOCKED: non-fast-forward divergence
  - 531 commits on remote not in local
  - 572 commits in local not in remote
  - Likely caused by prior history rewrite (secret purge) that was never force-pushed
  - DO NOT force-push without founder approval per `09_deployment_gate_stone.md` rule 4
