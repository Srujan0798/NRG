---
name: bug-hunt
description: Systematic root cause analysis for bugs. Use /bug-hunt [description of the bug or error message] to investigate.
allowed-tools: Bash(git *) Bash(.venv/bin/python *) Bash(pytest *) Read Grep Glob
---

# Bug Hunt — Systematic Root Cause Analysis

You are a detective. Don't guess. Follow the evidence.

## Protocol

### Step 1: Reproduce
```bash
# If it's a test failure:
cd /Users/srujansai/Desktop/NRG && PYTEST_CURRENT_TEST=1 .venv/bin/python -m pytest tests/ -k "$ARGUMENTS" -v --tb=long 2>&1 | tail -40

# If it's a runtime error — check recent logs and changes:
git log --oneline -10
git diff HEAD~3 --stat
```

### Step 2: Trace the Error Path

1. Read the EXACT error message and stack trace
2. Open the file at the EXACT line number
3. Trace backwards: what called this function? What data did it receive?
4. Check: did this work before? `git log -p --follow [file]`

### Step 3: Find the Root Cause

Ask these questions in order:
1. **Data problem?** — Is the input wrong? Check the caller.
2. **Logic problem?** — Is the code wrong? Check the algorithm.
3. **Integration problem?** — Are two systems disagreeing? Check interfaces.
4. **Environment problem?** — Missing dependency, wrong config? Check .env and imports.
5. **Race condition?** — Timing-dependent? Check async/await and shared state.

### Step 4: Produce Fix Protocol

```
## Bug Report

### Symptom
[What the user/test sees]

### Root Cause
[Exact file:line and why it's wrong]

### Fix
[Exact code change needed — what to change, in which file, at which line]

### Verification
[Exact test command to confirm the fix works]

### Prevention
[Should a new test, rule, or pre-commit check prevent this class of bug?]
```

Do NOT implement the fix. Produce the protocol for the execution agent.
