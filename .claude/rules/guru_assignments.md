# Guru Assignment Format Rule

> Binding on all Guru agents. Violation = invalid assignment.

## Rule 1: Read Shishya Format Before Assigning

Before creating ANY task, assignment, prompt stone, or instruction for a Shishya agent, the Guru **must** read `.agents/AGENTS.md` §Task Format (lines 111-120).

The canonical format is:

```
FILES      — What to read/modify
PROBLEM    — What's wrong
STEPS      — Sequential actions
SKILLS     — Which skills to activate
EVIDENCE   — What to produce
DONE WHEN  — Acceptance criteria
```

## Rule 2: No Ad-Hoc Formats

- Do NOT invent new formats (no "Fortify/Elevate/Immortalize", no "Guru Assignment Notes", no custom headers).
- Do NOT create `.claude/assignments/` files that deviate from the 6-line format.
- Do NOT give condensed prompts or paraphrased summaries. Point Shishya to the canonical file or paste the exact 6-line block.

## Rule 3: Cross-Reference, Don't Duplicate

If `.claude/assignments/` files exist, they must use the 6-line format from `.agents/AGENTS.md`. If they deviate, Guru must fix them, not create new ones.

## Rule 4: Skill References Must Be Exact Paths

SKILLS line must reference exact paths:
- `.agents/skills/<name>/SKILL.md` for execution skills
- `.claude/skills/<name>/SKILL.md` for strategy/sovereign skills

## Rule 5: Evidence Path Must Exist

EVIDENCE line must specify a concrete `evidence/YYYY-MM-DD/` path. No vague "save output" instructions.

## Enforcement

`nrg-verify-workflow.py` checks `.claude/assignments/*.md` for compliance with this format.
