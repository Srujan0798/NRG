---
name: test-suite
description: Run full test suite with coverage. Use /test-suite to run all tests, or /test-suite auth to run specific module.
allowed-tools: Bash(pytest *) Bash(.venv/bin/python *) Read Grep
---

# Test Suite

Run the NRG test suite and report results.

## Steps

1. Run tests:
```bash
cd /Users/srujansai/Desktop/NRG && PYTEST_CURRENT_TEST=1 .venv/bin/python -m pytest tests/ -v --tb=short -q $ARGUMENTS
```

2. If any tests fail:
   - Read the failing test file
   - Read the source file being tested
   - Identify root cause
   - Suggest a fix

3. Report: X passed, Y failed, Z skipped
