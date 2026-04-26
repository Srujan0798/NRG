---
name: Dhairya Benchmark Reference
description: External engineer's SQL audit is our gold-standard benchmark — 17 queries with ground-truth SQL, NOT our team member
type: reference
---

SesDhairya is an external engineer working on a similar project separately. He is NOT on the NRG team.

His report contains 17 real analytical queries with:
- Natural language question
- Expected ("Actual") SQL — the correct query
- AI-generated SQL — what the system produced
- Evaluation tags: xxx (correct), yyy (format mismatch), zzz (wrong), 000 (error)
- Response times and failure reasons

**Formatted report**: `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md`
**Failure analysis**: `docs/reports/sql_audit_dhairya.md` (7 failure patterns)
**Improvement plan**: `docs/reports/SQL_IMPROVEMENT_PLAN.md` (6 fixes applied, 3 remaining)
**Raw original**: `docs/reports/SQL_AUDIT_RAW_dhairya.sql`

**Agent applied fixes** (2026-04-23): schema synonyms, CTE templates, completeness validator, query context, anti-patterns, mandatory rules. All in `src/data/schema/` and `src/skills/text_to_sql/`.

**Use as**: regression benchmark for all Text-to-SQL changes. Target: 85% accuracy (currently 41% baseline).
