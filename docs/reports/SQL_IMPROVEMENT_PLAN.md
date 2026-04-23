# SQL Pipeline Improvement Plan — Based on Dhairya's Audit

**Generated from:** `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md`
**Date:** 2025-04-23
**Status:** All HIGH and MEDIUM priority items implemented in this session.

---

## Overview

Dhairya's audit tested 17 queries against the NRG Text-to-SQL pipeline. Results: **41% correct (7/17)**, **59% failure (10/17)**. Analysis revealed 7 distinct failure patterns. All HIGH and MEDIUM items below have been implemented.

---

## Priority Matrix

| Priority | Item | Pattern | Status |
|----------|------|---------|--------|
| HIGH | Schema synonym mapping (TRL, course level, institute names) | Q6, Q4 | ✅ Implemented |
| HIGH | CTE scaffolding for YoY, cost-per-unit, gap analysis | Q3, Q11, Q7 | ✅ Implemented |
| HIGH | Query completeness validator (HAVING, parentheses, trailing operators) | Q16, Q14 | ✅ Implemented |
| HIGH | Follow-up context tracking (maintain domain across turns) | Q10, Q12 | ✅ Implemented |
| HIGH | Credits format parsing (SPLIT_PART for "3:1" format) | Q1 | ✅ Implemented |
| MEDIUM | Cross-module join key mapping (institute vs applicants) | Q7 | ✅ Implemented |
| MEDIUM | Query retry on completeness failure | Q16 | ✅ Implemented |
| LOW | Response time optimization (< 3s SLO target) | All | Planned |
| LOW | Benchmark test suite from Dhairya's 17 queries | All | Planned |

---

## Implemented Changes

### 1. Schema Value Synonyms (`src/data/schema/schema_value_synonyms.md`) — NEW

Maps domain terms to canonical DB values. Prevents TRL 9 / Level 9 confusion.

**Contents:**
- TRL levels: `Level 9` = `TRL 9` = `Market Ready` = `TRL9`
- Course levels: `UG`, `PG`, `PhD` (with all synonyms)
- Credits format: `"3:1"` → `SPLIT_PART(total_credit_score, ':', 1)`
- Financial year: string format `'2022-23'`, not integer
- Patent status: `Granted`, `Filed`, `Examined`, `Rejected`
- Institute normalization: `LIKE '%IIT Madras%'`
- Cross-module join keys: always join on `institute`, never `applicants`

**Files affected:** `src/skills/text_to_sql/schema_extractor.py`

---

### 2. Enhanced Schema Hints (`src/data/schema/schema_hints.md`) — REWRITTEN

Added 8 SQL anti-patterns + 6 CTE scaffolding templates.

**Anti-patterns documented:**
1. `SELECT DISTINCT col ORDER BY col` — wrong for ranked results
2. Missing `GROUP BY` before `HAVING`
3. Row-level comparison instead of CTE aggregation
4. Trailing `-- [INCOMPLETE]` or missing HAVING
5. Wrong domain table on follow-up
6. Direct integer cast of `total_credit_score`
7. Joining on `applicants` instead of `institute`
8. Exact institute name when DB stores variations

**CTE Templates added:**
- Pattern A: Year-over-Year Growth
- Pattern B: Cost-Per-Unit (Grant per Patent)
- Pattern C: Gap Analysis (High Capex / Low Output)
- Pattern D: Utilization Audit (High Grants vs Expenditure)
- Pattern E: Pipeline Progression (TRL Stage Distribution)
- Pattern F: Cross-Module Correlation (Courses vs Startups)

---

### 3. Enhanced System Prompt (`src/skills/text_to_sql/skill.py`) — UPDATED

Replaced generic SQL expert prompt with domain-aware prompt including:

- **Domain synonyms** inline in prompt (TRL 9, UG/PG/PhD, etc.)
- **Aggregation rules** for YoY, cost-per-unit, top-N
- **Anti-patterns** listed explicitly
- **CTE scaffolding** reference
- **Follow-up rules** (maintain same domain)
- **Credits parsing** (SPLIT_PART rule)

---

### 4. QueryCompletenessValidator (`src/skills/text_to_sql/validator.py`) — NEW

Validates that generated SQL is syntactically complete before execution.

**Checks:**
- No `-- [INCOMPLETE]` markers
- Balanced parentheses
- No trailing `WHERE`/`AND`/`OR`/`ON` at end
- No trailing `,` or `+`
- `HAVING` without `GROUP BY` → flagged
- `ORDER BY` on raw column when aggregate ranking expected → flagged

**Auto-retry:** If query fails completeness check, `TextToSQLSkill.execute()` retries once with the issues injected into context.

---

### 5. QueryContext (`src/skills/text_to_sql/skill.py`) — NEW

Tracks conversation context across turns.

**Tracks:**
- Last used tables (prevents domain switching on follow-up)
- Last referenced institutes
- Query topic

**Use case:** When user asks "how does that compare" after Q9 (PhD courses), system knows to stay in `academic_courses_details`, not switch to `student_strength`.

---

### 6. Retry on Completeness Failure

`TextToSQLSkill.execute()` now:
1. Generates SQL with completeness validator check
2. If incomplete → retries once with issues injected as `[RETRY]` context
3. If still incomplete → logs error but proceeds (graceful degradation)

---

## Files Modified/Created

| File | Change |
|------|--------|
| `src/data/schema/schema_value_synonyms.md` | **NEW** — domain synonym mappings |
| `src/data/schema/schema_hints.md` | **REWRITTEN** — anti-patterns + CTE templates |
| `src/skills/text_to_sql/schema_extractor.py` | Loads and injects synonyms into LLM prompt |
| `src/skills/text_to_sql/skill.py` | Enhanced prompt, QueryContext, completeness retry |
| `src/skills/text_to_sql/validator.py` | Added QueryCompletenessValidator class |

---

## Remaining Work (LOW Priority)

### A. Response Time (Target: < 3s, Currently: ~7.2s)

Options:
- Pre-compute and cache frequently-used aggregations (funding by institute, course counts by level)
- Async query generation pipeline
- Schema extraction caching (don't re-extract on every query)

### B. Benchmark Test Suite

Create a test file with Dhairya's 17 queries as regression tests:
```
tests/skills/test_text_to_sql_regression.py
```
Run against every code change to detect prompt/pipeline regressions.

### C. Query Execution Time Per Phase

Current 7.2s is end-to-end. Break down by phase:
1. Schema extraction: ~1-2s
2. LLM call: ~4-5s
3. Validation: ~0.5-1s
4. Execution: varies

Target: reduce LLM call with better prompting and caching.

---

## Verification

All modified files:
- ✅ Compile (`python3 -m py_compile`)
- ✅ Pass lint (`ruff check`)
- ✅ Pass existing tests (audit: 11/11, schema: 5/5)

Pre-existing test failures (unrelated):
- `TestTierRateLimiting` — imports `_get_tier_key` that doesn't exist in `rate_limiter.py`
