---
name: pre-commit
description: Quality gate that EVERY agent must run before committing. Blocks commit if checks fail. Use /pre-commit to run.
allowed-tools: Bash(.venv/bin/python *) Bash(pytest *) Bash(python *) Bash(git *) Bash(npx *) Read Grep
---

# Pre-Commit Gate

Run this BEFORE every commit. If any CRITICAL check fails, DO NOT COMMIT.

## Checks (in order)

### 1. Python Lint
```bash
cd /Users/srujansai/Desktop/NRG && .venv/bin/python -m py_compile $(git diff --cached --name-only --diff-filter=ACM | grep '\.py$' | tr '\n' ' ') 2>&1
```
If py_compile fails → BLOCK. Syntax errors must not enter the repo.

### 2. Import Check
```bash
cd /Users/srujansai/Desktop/NRG && .venv/bin/python -c "
import sys; sys.path.insert(0, '.')
files = '$(git diff --cached --name-only --diff-filter=ACM | grep "^src/.*\.py$" | head -10)'.split()
for f in files:
    if f.strip():
        mod = f.replace('/', '.').replace('.py', '')
        try:
            __import__(mod)
            print(f'  OK: {mod}')
        except Exception as e:
            print(f'  FAIL: {mod} — {e}')
            sys.exit(1)
"
```
If imports fail → BLOCK. Broken imports break the entire system.

### 3. Fast Tests (changed files only)
```bash
cd /Users/srujansai/Desktop/NRG && PYTEST_CURRENT_TEST=1 .venv/bin/python -m pytest tests/ -x --tb=short -q --timeout=60 2>&1 | tail -5
```
If tests fail → BLOCK. Never commit broken tests.

### 4. Security Quick Scan
```bash
cd /Users/srujansai/Desktop/NRG
# Check for secrets in staged files
git diff --cached | grep -iE "(password|secret|api_key|token)\s*=" | grep -v "test\|example\|#\|environ\|getenv\|REPLACE_ME" && echo "POTENTIAL SECRET DETECTED — BLOCK" || echo "No secrets found — OK"
```
If secrets detected → BLOCK.

### 5. Audit Chain Integrity
```bash
cd /Users/srujansai/Desktop/NRG && .venv/bin/python -c "from src.audit import verify_chain; v, e = verify_chain(); print(f'Chain: {\"OK\" if v else \"CORRUPTED — \" + str(e[:3])}')"
```
If corrupted → WARN (don't block, but flag).

### 6. Schema Reference Check (if SQL/schema files changed)
```bash
cd /Users/srujansai/Desktop/NRG
# If any schema hint or SQL generation file was modified, verify it references prod schema
git diff --cached --name-only | grep -E "(schema_hints|schema_extractor|text_to_sql|schema_value)" && echo "SCHEMA FILES CHANGED — verify against db_struct.sql (58-table prod schema), not just 18-table SQLite" || echo "No schema files changed — OK"
```
If schema files changed → WARN: Agent must verify changes account for the 58-table PostgreSQL schema (`db_struct.sql`), not just the 18-table dev SQLite. See `.claude/CLAUDE.md` "THE 3 DATA SOURCES".

## Output
```
PRE-COMMIT GATE
  [PASS/FAIL] Syntax check
  [PASS/FAIL] Import check
  [PASS/FAIL] Tests (X passed, Y failed)
  [PASS/FAIL] Secret scan
  [PASS/WARN] Audit chain
  [PASS/WARN] Schema reference (if applicable)

VERDICT: CLEAR TO COMMIT / BLOCKED — fix issues above
```
