# D4-09 Data Quality Baseline Compare

- May 1 baseline: `evidence/2026-05-01/data_quality_closure/scorecard_final.json`
- Current run: `evidence/2026-05-02/batch4_data_sql_schema/D4-09_data_quality_scorecard.json`

| Metric | May 1 Baseline | Current |
|---|---:|---:|
| Overall status | PASS | PASS |
| Overall score | 0.9039 | 0.9427 |
| Alerts | 0 | 0 |

Current rerun source: `scripts/data_quality_scorecard.py` against local
PostgreSQL after the current freshness exclusions for audit and backup tables.
Schema coverage, referential integrity, null rate, freshness, completeness,
consistency, and PII sanitization all passed.
