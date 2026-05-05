# NRG Hybrid Assignment Template

> Canonical assignment format for Guru → Shishya handoff.
> Combines Codex 5.5 cognitive framing (Role, Personality, Goal, Constraints, Stop Rules)
> with NRG execution mechanics (FILES, PROBLEM, STEPS, SKILLS, EVIDENCE, DONE WHEN).
>
> Copy this file. Replace bracketed placeholders. Save to `.claude/assignments/shishya_<task>.md`.

---

# ASSIGNMENT: [Task Name]

## Role

[1-2 sentences defining who the agent is, what context they have, and what their job is for this task. Be specific: "You are a backend engineer fixing the text-to-SQL pipeline" not "You are an AI assistant."]

## Personality

[tone, demeanor, and collaboration style for this specific task]
- How to treat uncertainty: [ask vs. assume vs. research]
- How to treat mistakes: [fix silently vs. report vs. escalate]
- How to treat the codebase: [conservative vs. aggressive refactoring]

## Goal

[User-visible outcome. One sentence. What changes in the world when this is done?]

## Context

**FILES** — What to read/modify:
- `[file path]` — [why read this]
- `[file path]` — [why read this]
- `[file path]` — [why read this]

**PROBLEM** — What's wrong:
[Clear, specific statement of the bug, gap, or missing feature. Include exact error messages, line numbers, or audit findings.]

## Execution

**STEPS** — Sequential actions:
1. [action] — [expected result / how to verify]
2. [action] — [expected result / how to verify]
3. [action] — [expected result / how to verify]
4. [action] — [expected result / how to verify]

**SKILLS** — Which skills to activate:
- `.agents/skills/[name]/SKILL.md` — [how applied to this task]
- `.claude/skills/[name]/SKILL.md` — [how applied to this task]

## Constraints

[policy, safety, business, evidence, and side-effect limits]
- Do not [forbidden action]
- Must [required action before claiming done]
- Never [absolute limit that triggers STOP]
- If [condition] then [required response]

## Output

**EVIDENCE** — What to produce:
`evidence/YYYY-MM-DD/[task_id]/`
- `00_summary.md` — what changed, why, commit SHA
- `01_[artifact]` — [specific content expected]
- `02_[artifact]` — [specific content expected]
- `03_[artifact]` — [specific content expected]

**DONE WHEN** — Acceptance criteria:
- [ ] [Criterion 1: measurable, verifiable]
- [ ] [Criterion 2: measurable, verifiable]
- [ ] [Criterion 3: measurable, verifiable]
- [ ] [Criterion 4: measurable, verifiable]

## Stop Rules

- If [condition X] → [action: retry / fallback / abstain / ask / stop]
- If [condition Y] → [action]
- If blocked after [N] attempts → STOP and report to Guru with [specific artifacts]
- If you would violate any Constraint → STOP and ask Guru before proceeding
