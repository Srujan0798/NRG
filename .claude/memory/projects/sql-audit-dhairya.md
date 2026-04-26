---
name: Dhairya SQL Audit & Agent Fixes
description: External 17-query eval (41% accuracy), agent implemented 6 fixes — schema synonyms, CTE templates, completeness validator, query context
type: project
---

**Source:** SesDhairya (external engineer working on similar project) ran 17 analytical queries on 2026-04-23.
**Results:** 7 correct (41%), 2 format issues (12%), 5 wrong (29%), 3 errors (18%). Avg response time: 7.2s (SLO target: <3s).

**Why:** First real-world eval with ground-truth SQL. This is NRG's benchmark dataset. Dhairya is NOT on our team — his report is external intelligence we're using to improve.

**How to apply:** These 17 queries are the gold standard for Text-to-SQL accuracy. All improvements should be validated against them.

**7 Failure Patterns Identified:**
1. Incorrect aggregation (Q3, Q11) — row-level vs GROUP BY sums
2. Missing/late HAVING (Q14, Q16) — truncated multi-stage queries
3. Cross-domain confusion (Q10, Q12) — wrong table on follow-up
4. String value mismatch (Q6) — 'TRL 9' vs 'Level 9'
5. ORDER BY/LIMIT errors (Q1, Q4) — DISTINCT instead of aggregate ranking
6. JOIN key mismatch (Q7, Q13) — applicants vs institute
7. Complete failure (Q15) — complex multi-step reasoning

**Agent Fixes Applied (2026-04-23):**
- `src/data/schema/schema_value_synonyms.md` — NEW: domain synonym mappings (TRL, course levels, agencies, fiscal year formats)
- `src/data/schema/schema_hints.md` — REWRITTEN: 7 anti-patterns + 6 CTE scaffold templates + 5 mandatory rules
- `src/skills/text_to_sql/schema_extractor.py` — Tier column visibility, schema probing detection, synonym injection into LLM prompt
- `src/skills/text_to_sql/skill.py` — Enhanced prompt, QueryContext for follow-ups, completeness retry
- `src/skills/text_to_sql/validator.py` — QueryCompletenessValidator (balanced parens, trailing operators, HAVING without GROUP BY)

**Remaining:**
- Benchmark test suite (17 queries as regression tests) — NOT yet created
- Response time optimization (7.2s → <3s target) — NOT yet done
- Re-run Dhairya's 17 queries to measure improvement — NEEDED

**Files:**
- Formatted report: `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md`
- Failure analysis: `docs/reports/sql_audit_dhairya.md`
- Improvement plan: `docs/reports/SQL_IMPROVEMENT_PLAN.md`
- Raw report: `docs/reports/SQL_AUDIT_RAW_dhairya.sql`
- Original file: `sesDhairya's report:.sql`
