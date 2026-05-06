# Killer Query PostgreSQL Seed — Evidence

Date: 2026-05-06
Status: PASS — All 4 tables seeded, all 3 killer queries return data

## Tables Seeded

| Table | Row Count |
|-------|-----------|
| innovations_at_various_stages_of_technology_readiness_level | 1,440 |
| innovation_grant_from_govt | 280 |
| combined_ipo_patent_data | 282 |
| academic_courses_details | 3,840 |

## Killer Query Verification

### K-Q1 (IIT highest innovation credits FY 2022-23)
Returns IIT Kharagpur, IIT Kanpur, IIT Delhi with 474 credits each.
SQL: `SELECT institute, SUM(CAST(total_credit_score AS NUMERIC)) ... WHERE financial_year = '2022-23' GROUP BY institute ORDER BY total_credits DESC`

### K-Q2 (IIT Madras TRL progression Level 4 → Level 9)
Returns 11.1% market-ready (Level 9) across 4 years for IIT Madras.
SQL: `SELECT financial_year, COUNT(*) FILTER (WHERE stage_of_technology = 'Level 9') / COUNT(*) ... WHERE institute = 'IIT Madras'`

### K-Q3 (Institutes cut grants >40% yet increased patents)
Returns IIT Delhi (-70.6% grant drop, +28.6% patent growth) and IIT Hyderabad (-63%, +28.6%).
SQL: CTEs grant_yoy + patent_yoy, HAVING grant_drop_pct < -40 AND patent_growth_pct > 0

## Seed Script
`scripts/seed_killer_query_tables_pg.py` — idempotent (uses ON CONFLICT DO NOTHING)
Run with: `python3 scripts/seed_killer_query_tables_pg.py`
