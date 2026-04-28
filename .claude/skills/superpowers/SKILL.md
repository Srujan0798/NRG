---
name: superpowers
description: Structured software development methodologies — TDD (red-green-refactor), systematic debugging (4-phase), Socratic brainstorming, subagent-driven development with code review, and skill authoring. Invoke sub-skills via /tdd, /debug, /brainstorm, /execute-plan, /write-skill.
model-agnostic: true
sub-skills: tdd · debug · brainstorm · execute-plan · write-skill · code-reviewer
---

# Superpowers

Composable development disciplines. Each sub-skill enforces a specific methodology. Never skip phases.

---

## /brainstorm — Socratic Requirements Refinement

Use BEFORE writing any code. Refine requirements through questioning before implementation begins.

**Process:**
1. Restate what you understand the requirement to be
2. Ask 3–5 clarifying questions that expose ambiguity, edge cases, or hidden constraints
3. Wait for answers. Do not proceed to design until answered.
4. Produce a refined requirements statement + acceptance criteria
5. Get explicit approval before moving to implementation

**For NRG:** Before any query feature, ask: Which tier? What's the RBAC boundary? Does it touch PII columns? What's the evidence requirement?

**Anti-pattern:** Starting to code before requirements are crisp. If you find yourself writing code before brainstorming is complete — stop.

---

## /tdd — Red-Green-Refactor

Tests must FAIL before implementation. No exceptions.

**Cycle:**
```
RED:    Write a test that fails for the right reason
        → Run it. Confirm it fails. If it passes, the test is wrong.
GREEN:  Write the minimum code to make it pass
        → No gold-plating. Minimum viable implementation only.
REFACTOR: Clean up while keeping tests green
        → Improve readability, remove duplication, no new behavior
```

**Rules:**
- Never write implementation before a failing test exists
- One failing test at a time
- If you can't make a test fail — you don't understand the requirement yet
- Commit at GREEN before refactoring

**For NRG:**
```bash
# Confirm test fails first
PYTEST_CURRENT_TEST=1 .venv/bin/python -m pytest tests/path/test_file.py::test_name -v
# Should show FAILED — then write implementation
```

**Forbidden:** Writing tests after implementation to match known output. That's not TDD, it's theater.

---

## /debug — 4-Phase Systematic Debugging

Never guess. Never apply a fix before completing root cause analysis.

**Phase 1 — REPRODUCE**
- Produce a minimal, deterministic reproduction case
- If you can't reproduce it reliably, you don't understand it yet
- Document: exact input → exact output → expected output

**Phase 2 — ROOT CAUSE**
- Trace execution path from symptom back to origin
- List hypotheses ranked by probability
- Do NOT fix anything yet

**Phase 3 — HYPOTHESIS TEST**
- Test each hypothesis with the minimal change that would confirm/deny it
- Eliminate hypotheses one by one
- Document what each test revealed

**Phase 4 — FIX + VERIFY**
- Apply fix only after root cause is confirmed
- Write a test that fails without the fix, passes with it
- Verify fix doesn't break adjacent behavior

**Safeguard:** If 3 fix attempts fail → trigger architectural review. The bug is a symptom of a design problem.

**For NRG:** Most bugs are in one of: tier RBAC boundary, audit chain event ordering, SQL alias (trl_stages), or PII detection false positive/negative. Check these first.

---

## /execute-plan — Batched Implementation with Review Checkpoints

For multi-step features. Breaks work into reviewable chunks.

**Format:**
```
PLAN:
  Step 1: [what + acceptance criteria]
  Step 2: [what + acceptance criteria]
  Step 3: [what + acceptance criteria]

CHECKPOINT after each step:
  - Tests passing?
  - Code reviewer sign-off?
  - Evidence committed?
  → If NO on any → fix before proceeding
```

**Code Reviewer Agent** (runs at each checkpoint):
Evaluates implementation against:
- The original plan — did you implement what was agreed?
- Coding standards — does it follow project conventions?
- Architectural principles — does it fit the existing patterns?
- Test coverage — is the new behavior tested?

Output: APPROVED / NEEDS REVISION + specific feedback.

---

## /write-skill — Skill Authoring with TDD

Apply TDD principles to documentation/skills.

**Process:**
1. Define the skill's trigger (when should an agent use this?)
2. Write the acceptance test: "Given [situation], skill produces [output]"
3. Write a minimal SKILL.md that would pass the acceptance test
4. Test it: give the skill to an agent, run the trigger scenario
5. Refactor: improve clarity without changing behavior
6. Register in AGENTS.md or CLAUDE.md skills directory

**SKILL.md structure:**
```markdown
---
name: skill-name
description: One line — when to use + what it does
---
# Skill Name
## Trigger / When to use
## Process (numbered steps)
## Output format
## For NRG (project-specific notes)
## Anti-patterns
```

---

## For NRG Usage

| Situation | Sub-skill |
|---|---|
| New feature request arrives | `/brainstorm` first, always |
| Writing any test or fix | `/tdd` — confirm RED before GREEN |
| Bug report from agent or evidence | `/debug` — 4 phases, no guessing |
| Multi-step K-* protocol | `/execute-plan` with checkpoints |
| Need a new NRG skill | `/write-skill` |
