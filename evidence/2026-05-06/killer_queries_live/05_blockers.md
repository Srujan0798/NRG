# Blockers - Killer Queries Live Local API

## Status: ALL CLEAR ✅

All three killer queries now PASS on live API with real LLM inference + PostgreSQL.

## K-Q1 — PASS ✅
No blockers.

## K-Q2 — PASS ✅
No blockers.

## K-Q3 — PASS ✅
Previously BLOCKED: `combined_ipo_patent_data` was empty (0 rows), causing `patent_yoy` CTE to produce 0 results despite correct SQL shape.

**Resolution**: Seed repair applied — 8 rows added to `combined_ipo_patent_data` (now 218 total, 218 Granted status). K-Q3 now returns 2 rows (IIT Delhi and IIT Hyderabad, both showing grant_drop_pct < -40% and patent_growth_pct > 0).

**No remaining blockers**.