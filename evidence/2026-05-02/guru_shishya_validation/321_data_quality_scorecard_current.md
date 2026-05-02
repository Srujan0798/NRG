# Data Quality Scorecard

- Generated: `2026-05-02T11:41:06.270073+00:00`
- Database: `postgresql://nrg:***@localhost:5432/nrg`
- Overall: `PASS` (0.883)

| Pillar | Status | Score | Threshold | Detail |
| --- | --- | ---: | --- | --- |
| `schema_coverage` | PASS | 1.000 | >= 58 expected tables present | 58/58 expected tables present |
| `referential_integrity` | PASS | 1.000 | >= 99.00% valid references | 0 orphaned references across 0 checked |
| `null_rate` | PASS | 1.000 | <= 5.00% nulls in any measured column | worst column null rate 0.000 |
| `freshness` | PASS | 0.181 | <= 7 days since latest update | worst table age 5.731 days |
| `completeness` | PASS | 1.000 | >= 1000 rows in every core table | 0 core tables below minimum row count |
| `consistency` | PASS | 1.000 | cross-table validations have zero orphaned references | 0 cross-table consistency violations |
| `pii_sanitization` | PASS | 1.000 | 0 PII findings in non-PII tables | 0 PII findings in non-PII tables |
