# FIX-GAP-B-001 — vector_drift_scheduler.py Test Coverage
Date: 2026-04-25
Task: Create scripts/vector_drift_scheduler.py (60s loop, calls drift check, emits to /api/reindex). Add test.

## Verification
```bash
$ PYTEST_CURRENT_TEST=1 .venv/bin/python -m pytest tests/scripts/test_vector_drift_scheduler.py -v
# 11 passed in 2.77s
```

## Test Coverage
| Test | Description |
|------|-------------|
| test_triggers_when_reindex_info_flag_set | reindex_triggered=True always triggers |
| test_triggers_when_max_shift_breaches_threshold | max_shift > COSINE_SHIFT_THRESHOLD (0.05) triggers |
| test_triggers_when_drift_alert_warning | WARNING alert_level triggers |
| test_triggers_when_drift_alert_critical | CRITICAL alert_level triggers |
| test_no_trigger_when_stable_and_no_flags | STABLE + no flags = no trigger |
| test_run_once_calls_check_fn | run_once calls check_fn and returns drift |
| test_run_once_triggers_reindex_when_needed | CRITICAL triggers reindex_fn call |
| test_run_once_no_trigger_when_stable | STABLE does not call reindex_fn |
| test_loop_runs_max_iterations | loop runs exactly max_iterations |
| test_loop_returns_schedulerrun_list | returns list of SchedulerRun objects |
| test_interval_must_be_positive | raises ValueError for interval_seconds <= 0 |

## Files Created
- `tests/scripts/test_vector_drift_scheduler.py` — 11 tests
- `tests/scripts/conftest.py` — adds scripts/ to sys.path for imports

## Status: ✅ PASS — script exists and has 11 passing tests.

---

# VERIFY-GAP-C-001 — HALL_OF_SHAME Pattern Verification
Date: 2026-04-25
Task: Verify HALL_OF_SHAME.md has all 7 Dhairya patterns with real SQL.

## Verification
```bash
$ wc -l src/data/schema/failed_queries/HALL_OF_SHAME.md
195 src/data/schema/failed_queries/HALL_OF_SHAME.md

$ grep "^## P" src/data/schema/failed_queries/HALL_OF_SHAME.md
## P1: SPLIT_PART Format Blind (Q1)
## P2: DISTINCT vs GROUP BY Confusion (Q4)
## P3: Row-Level vs Aggregated YoY (Q3, Q11)
## P4: Missing or Truncated HAVING (Q14, Q16)
## P5: Cross-Domain Follow-Up Confusion (Q10, Q12)
## P6: TRL Synonym Blindness (Q6)
## P7: Multi-Step Reasoning Failure (Q15)
```

## Pattern Coverage
| Pattern | Queries | Fix Description |
|---------|---------|----------------|
| P1 SPLIT_PART | Q1 | Parse "3:1" credit format before aggregation |
| P2 DISTINCT vs GROUP BY | Q4 | Use GROUP BY + ORDER BY SUM() for ranked metrics |
| P3 Row-Level vs Aggregated YoY | Q3, Q11 | CTE with GROUP BY institute,year then self-join |
| P4 Missing/Truncated HAVING | Q14, Q16 | completeness_validator rejects incomplete SQL |
| P5 Cross-Domain Follow-Up | Q10, Q12 | NRGState.active_domain persists table context |
| P6 TRL Synonym Blindness | Q6 | Synonym map: TRL9/Level9/Market Ready → "Level 9" |
| P7 Multi-Step Reasoning | Q15 | CTE for institute funding + global avg comparison |

## Status: ✅ PASS — all 7 patterns present with real SQL fixes and test references.
