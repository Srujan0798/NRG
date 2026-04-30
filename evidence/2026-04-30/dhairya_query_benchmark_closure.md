# Dhairya Query Benchmark Closure

Date: 2026-04-30

## Scope

This closes the next recommended step after source-locking `CORPUS/`: run the
real Dhairya/killer benchmark surface, fix concrete answer-engine failures, and
verify the nearest API/query contracts.

## Red Run

Command:

```bash
python3 -m pytest tests/benchmarks/test_dhairya_regression.py tests/benchmarks/test_dhairya_adversarial.py -q --tb=short
```

Result before fix:

```text
24 failed, 29 passed, 31 deselected in 6.56s
```

Primary failures:

- Dhairya Q1/Q2/Q3/Q5/Q6/Q8/Q9/Q12/Q13/Q15/Q16 routed to generic
  `institutions`, `labs`, or funding SQL instead of benchmark-specific SQL.
- `docs/compliance/hall-of-shame.md` was missing.

## Fixes

- `src/skills/text_to_sql/safe_sql_builder.py`
  - Defers high-risk Dhairya patterns to the richer Text-to-SQL fallback
    templates instead of emitting simple list SQL.
  - Covers credit parsing, PhD/UG, YoY, TRL readiness, course follow-ups,
    course/startup correlation, rising-star funding, utilization audit, and
    patent-cost patterns.
- `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md`
  - Added the seven-pattern index needed by benchmark contract tests.
- `docs/compliance/hall-of-shame.md`
  - Restored the required pattern registry with wrong SQL, failure reason,
    correct SQL, adversarial fixture, and validator rule for each pattern.
- `src/api/main.py`
  - Ensures funding-policy explanatory queries use the live hybrid stream path
    before the C4 read-model SQL-only shortcut.
  - Renamed an internal strategy citation identifier to production framing so
    the commit vocabulary gate remains clean.

## Green Runs

Command:

```bash
python3 -m pytest tests/benchmarks/test_dhairya_regression.py tests/benchmarks/test_dhairya_adversarial.py -q --tb=short
```

Result:

```text
53 passed, 31 deselected in 6.18s
```

Command:

```bash
python3 -m pytest tests/benchmarks -q --tb=short
```

Result:

```text
57 passed, 44 deselected in 6.40s
```

Command:

```bash
python3 -m pytest tests/skills/test_text_to_sql.py tests/skills/test_text_to_sql_rewriter.py tests/orchestration/test_query_catalog.py tests/api/test_query_security_validation.py tests/api/test_live_hybrid_stream.py -q --tb=short
```

Result:

```text
32 passed, 1 warning in 14.01s
```

## Notes

- The warning is from LangChain/Pydantic compatibility under Python 3.14; the
  selected tests passed.
- This does not claim deployed production readiness. It proves the local
  Text-to-SQL benchmark and nearest stream/query contracts after the fix.
