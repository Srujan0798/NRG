# Guru Assignment Format Rule

> Binding on all Guru agents. Violation = invalid assignment.

## Rule 1: Use the Hybrid Template

Before creating ANY task, assignment, prompt stone, or instruction for a Shishya agent, the Guru **must** read `.claude/assignment_template.md`.

The hybrid format combines Codex 5.5 cognitive framing with NRG execution mechanics:

```
Role          — Who the agent is for this task
Personality   — Tone, demeanor, collaboration style
Goal          — User-visible outcome
Context
  FILES       — What to read/modify
  PROBLEM     — What's wrong
Execution
  STEPS       — Sequential actions
  SKILLS      — Which skills to activate
Constraints   — Policy, safety, evidence, side-effect limits
Output
  EVIDENCE    — What to produce
  DONE WHEN   — Acceptance criteria
Stop Rules    — When to retry, fallback, abstain, ask, or stop
```

## Rule 2: No Ad-Hoc Formats

- Do NOT invent new formats (no "Fortify/Elevate/Immortalize", no "Guru Assignment Notes", no custom headers).
- Do NOT create `.claude/assignments/` files that deviate from `.claude/assignment_template.md`.
- Do NOT give condensed prompts or paraphrased summaries. Point Shishya to the canonical file or paste the exact assignment block.

## Rule 3: Cross-Reference, Don't Duplicate

If `.claude/assignments/` files exist, they must use the hybrid format. If they deviate, Guru must fix them, not create new ones.

## Rule 4: Skill References Must Be Exact Paths

SKILLS line must reference exact paths:
- `.agents/skills/<name>/SKILL.md` for execution skills
- `.claude/skills/<name>/SKILL.md` for strategy/sovereign skills

## Rule 5: Evidence Path Must Exist

EVIDENCE line must specify a concrete `evidence/YYYY-MM-DD/` path. No vague "save output" instructions.

## Rule 6: Stop Rules Are Mandatory

Every assignment must include Stop Rules. Shishya agents must not loop forever or silently violate constraints.

## Rule 7: Update CURRENT_STATE.md After Assignment

After creating an assignment, update `.claude/CURRENT_STATE.md`:
- Mark the item as **Assigned** with the assignment filename
- Set **Owner** to the Shishya agent name or "pending"

## Enforcement

`nrg-verify-workflow.py` checks `.claude/assignments/*.md` for compliance with the hybrid format and validates that referenced skill files exist.
