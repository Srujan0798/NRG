---
name: docs-sync
description: Keep documentation aligned with actual code. Detect drift between README, Core_Idea_Clean.md, API docs, and the real codebase. Use /docs-sync to check.
allowed-tools: Bash(git *) Bash(.venv/bin/python *) Read Grep Glob
---

# Docs Sync — Drift Detection

Documentation that lies is worse than no documentation. Find the lies.

## Checks

### 1. README vs Reality
Read README.md and verify:
- Are the listed endpoints real? Check against `grep -n "@app\." src/api/main.py`
- Are the database counts accurate? Check against `sqlite3 src/data/nrg_research.db "SELECT COUNT(*) FROM researchers"`
- Are the setup instructions correct? Do the commands actually work?
- Are the listed features actually implemented?

### 2. Core_Idea_Clean.md vs Code
Read Core_Idea_Clean.md and verify:
- Phase checkboxes: are checked items actually done in code?
- File paths in "Agent Quick Reference": do they exist?
- Architecture description: does it match the actual graph.py flow?

### 3. .env.example vs .env
```bash
cd /Users/srujansai/Desktop/NRG
# Keys in .env.example
grep "^[A-Z]" .env.example | cut -d= -f1 | sort > /tmp/env_example_keys
# Keys in .env
grep "^[A-Z]" .env | cut -d= -f1 | sort > /tmp/env_keys
# Missing from example
comm -13 /tmp/env_example_keys /tmp/env_keys
# Extra in example (not used)
comm -23 /tmp/env_example_keys /tmp/env_keys
```

### 4. API Endpoints — Frontend vs Backend
```bash
# What the frontend calls
grep -rn "fetch\|axios\|/api/" frontend/src/ --include="*.ts" --include="*.tsx" | grep -oE '"/[^"]+"|`/[^`]+`' | sort -u

# What the backend serves
grep -n "@app\.\(get\|post\|put\|delete\)" src/api/main.py
```
Flag any frontend call that has no matching backend route.

## Output
```
DOCS SYNC REPORT

### Accurate (✓)
- [doc]: [claim] matches code

### DRIFT DETECTED (✗)
- [doc:line]: Claims [X] but code shows [Y]
  Fix: Update [doc or code] to say [correct thing]

### Missing Documentation
- [feature] exists in code but not documented anywhere
```

Produce fix protocols — do NOT make the changes yourself.
