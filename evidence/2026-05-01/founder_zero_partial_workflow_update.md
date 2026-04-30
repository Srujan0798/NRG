# Founder Zero-Partial Workflow Update

Date: 2026-05-01
Starting commit: `ec450ad fix: close validation campaign gaps`

## Founder Correction Captured

The founder correction is now encoded as a reusable workflow rule:

- Do not treat external v1.0 inventory as product proof.
- Do not treat useful idea integration as product proof.
- Do not answer superiority questions with reassurance.
- Do not claim NRG is stronger than an external v1.0 app across every corner unless a current
  proof matrix exists.
- If one surface is untested, mark it `UNKNOWN` or `BLOCKED`.
- If one surface fails, report it as a blocker and fix/retest before claiming.

## Files Updated

- Claude hybrid release fusion skill
  - Added `Founder Superiority Gate`.
  - Added required evidence matrix covering appearance, UI/UX, query
    intelligence, DB/schema, Dhairya SQL audit, backend/API, retrieval,
    security/tier, audit, accessibility, performance, evidence, and production.
- `.claude/skills/nrg-validation-campaign/SKILL.md`
  - Added `Founder Zero-Partial Gate`.
  - Requires every superiority row to be marked `PASS`, `FAIL`, `BLOCKED`, or
    `UNKNOWN`.
- `.agents/skills/nrg-validation-campaign/SKILL.md`
  - Added the same execution-agent rule in compressed form.
- `prompts_hybrid/08_full_coverage_validation_campaign_stone.md`
  - Added `Founder Zero-Partial Directive`.
  - Added the full required superiority matrix.
- `.claude/CLAUDE.md`
  - Added session-start hard rule for founder superiority questions.
- `.agents/AGENTS.md`
  - Added execution-agent hard rule for v1.0 fusion/superiority questions.
- `.claude/CURRENT_STATE.md`
  - Updated after verification to point future agents to this evidence.

## New Agent Behavior Required

When future agents receive a request like:

> Is NRG now 100% better than this external v1.0 app across appearance, UI/UX, DB, backend,
> accessibility, speed, and every corner?

They must answer with a proof matrix, not a blanket yes.

Example status shape:

| Surface | Status | Evidence or next command |
| --- | --- | --- |
| Appearance | PASS/FAIL/BLOCKED/UNKNOWN | path or command |
| UI/UX | PASS/FAIL/BLOCKED/UNKNOWN | path or command |
| Query intelligence | PASS/FAIL/BLOCKED/UNKNOWN | path or command |
| DB/schema | PASS/FAIL/BLOCKED/UNKNOWN | path or command |
| Dhairya SQL audit | PASS/FAIL/BLOCKED/UNKNOWN | path or command |
| Backend/API | PASS/FAIL/BLOCKED/UNKNOWN | path or command |
| Retrieval | PASS/FAIL/BLOCKED/UNKNOWN | path or command |
| Security/tier | PASS/FAIL/BLOCKED/UNKNOWN | path or command |
| Audit | PASS/FAIL/BLOCKED/UNKNOWN | path or command |
| Accessibility | PASS/FAIL/BLOCKED/UNKNOWN | path or command |
| Performance | PASS/FAIL/BLOCKED/UNKNOWN | path or command |
| Evidence | PASS/FAIL/BLOCKED/UNKNOWN | path or command |
| Production | PASS/FAIL/BLOCKED/UNKNOWN | path or command |

## Claim Boundary

Allowed after this update:

- The workflow now permanently records the founder's zero-partial quality gate.
- Future fusion and validation agents have explicit instructions for superiority
  claims.

Not allowed from this update alone:

- NRG is now perfect.
- NRG is proven stronger than every external v1.0 app across every surface.
- Production readiness is proven.

Those claims still require the validation matrix and deployed proof described in
`prompts_hybrid/08_full_coverage_validation_campaign_stone.md`.
