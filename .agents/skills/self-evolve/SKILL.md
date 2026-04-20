---
name: self-evolve
description: GUARDIAN evolution — analyzes what happened in the last sprint/cycle, updates rules, memory, CLAUDE.md, and skills to prevent repeat failures. Use /self-evolve after each sprint.
allowed-tools: Bash(git *) Bash(.venv/bin/python *) Bash(pytest *) Read Grep Glob Edit Write
---

# Self-Evolution — Guardian Agent

You are the system's immune system. After every sprint, you analyze what happened and make the system smarter.

## Evolution Protocol

### Step 1: Gather Evidence
```bash
# What changed this sprint?
git log --since="2 weeks ago" --oneline --stat

# What tests failed recently?
git log --since="2 weeks ago" --all --grep="fix:" --oneline

# What was the test pass rate?
cd /Users/srujansai/Desktop/NRG && PYTEST_CURRENT_TEST=1 .venv/bin/python -m pytest tests/ -q --tb=no 2>&1 | tail -3
```

### Step 2: Pattern Analysis

Look for:
1. **Recurring bugs**: Same type of fix appearing multiple times → need a NEW RULE
2. **Test gaps**: Features that shipped without tests → need coverage enforcement
3. **Security near-misses**: Anything that almost leaked PII or broke auth → need stronger gates
4. **Performance regressions**: Things getting slower → need benchmarks
5. **Architecture drift**: Code not following established patterns → need updated CLAUDE.md

### Step 3: Update the System

For each pattern found:

**If it's a code convention** → Update `.claude/rules/backend.md` or `frontend.md`:
```
Read the current rules file, add the new rule with WHY it exists.
```

**If it's a project-wide pattern** → Update `.claude/CLAUDE.md`:
```
Add to the DO NOT section or the Architecture Patterns section.
```

**If it's a recurring mistake** → Update memory:
```
Write to ~/.claude/projects/.../memory/bugs_patterns.md
Include: what the bug was, why it happened, how to prevent it.
```

**If it's a workflow improvement** → Update the relevant skill:
```
Add a new check to /pre-commit, or a new section to /code-review.
```

**If it's a sprint learning** → Update memory:
```
Write to ~/.claude/projects/.../memory/sprint_retrospective.md
Include: what worked, what didn't, what to do differently.
```

### Step 4: Produce Evolution Report

```
## Evolution Report — Sprint [N]

### New Rules Added
- [rule]: [why]

### Memory Updated
- [file]: [what changed]

### Skills Updated
- [skill]: [what was added]

### Metrics
- Tests: X passed / Y failed (trend: improving/degrading)
- Coverage: X% (trend)
- Security issues found: N (trend)
- Commits this sprint: N
- Bugs fixed: N
- Features shipped: N

### Recommendation for Next Sprint
[What to focus on based on the data]
```

### Step 5: Verify No Regressions
```bash
cd /Users/srujansai/Desktop/NRG && PYTEST_CURRENT_TEST=1 .venv/bin/python -m pytest tests/ -q --tb=short 2>&1 | tail -5
```
If the evolution changes broke anything → revert and flag.
