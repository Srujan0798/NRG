---
name: skill-creator
description: Create, improve, evaluate, and benchmark NRG skills. Use when authoring a new SKILL.md, upgrading an existing one, or measuring whether a skill actually improves agent output.
model-agnostic: true
---

# Skill Creator

## When to Create a New Skill

Create a skill when:
- An agent repeats the same multi-step process across sessions
- A pattern exists that prevents bugs when followed (e.g., trl_stages VIEW before SQL exposure)
- An external tool/API has a non-obvious usage pattern
- A domain rule needs to survive context window resets

Don't create a skill when:
- The pattern is a one-time fix
- It's already covered by an existing skill (check AGENTS.md first)

## SKILL.md Template

```markdown
---
name: skill-name
description: ONE LINE — trigger condition + what it produces. This is what agents see in the skill list.
model-agnostic: true
---

# Skill Name

## When to Use
[Exact trigger — "use when X", "use before Y", "use if Z"]

## Process
1. [Step with exact command or code pattern]
2. [Step]
3. [Step]

## Output
[What the skill produces — format, location, evidence]

## For NRG
[Project-specific notes — which files, which tiers, which constraints apply]

## Anti-Patterns
[What NOT to do — the failure modes this skill prevents]
```

## Placement Rules

| Skill type | Location |
|---|---|
| Strategy, planning, Guru-level | `.claude/skills/` |
| Execution, coding, agent-level | `.agents/skills/` |
| NRG-sovereign (audit, RBAC, DPDP) | `.claude/skills/nrg-*/` |

## Quality Bar for a SKILL.md

A skill is good when:
- [ ] Description fits in one line and says WHEN to use it (not just what it does)
- [ ] Process steps are numbered and each has an exact action (command, file, code)
- [ ] Has an anti-patterns section
- [ ] Has a "For NRG" section with project-specific context
- [ ] Is model-agnostic (no Claude-specific syntax unless in a note)
- [ ] Under 150 lines — if longer, split into sub-skills

## Evaluating a Skill

After writing, test it:
1. Give it to an agent with only the SKILL.md and a trigger scenario
2. Does the agent produce the right output without extra guidance?
3. Does it avoid the documented anti-patterns?
4. If agent fails → the skill is incomplete. Find the gap and fix it.

## Registering a New Skill

After writing:
1. Add to `.agents/AGENTS.md` skills table (correct category)
2. Add to `.claude/CLAUDE.md` skills directory section
3. Update `.claude/CURRENT_STATE.md` if it closes a gap

## Improving an Existing Skill

When an agent misuses a skill:
1. Read the SKILL.md — is the trigger ambiguous?
2. Read the agent's output — what did they misunderstand?
3. Add a clarifying line to the relevant section
4. Add the failure mode to Anti-Patterns
5. Don't rewrite — surgical additions only
