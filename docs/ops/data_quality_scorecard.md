# Data Quality Scorecard

- Generated: `2026-05-01T09:34:50.147356+00:00`
- Database: `postgresql://nrg:***@localhost:5432/nrg`
- Overall: `FAIL` (0.607)

| Pillar | Status | Score | Threshold | Detail |
| --- | --- | ---: | --- | --- |
| `schema_coverage` | PASS | 1.000 | >= 58 expected tables present | 58/58 expected tables present |
| `referential_integrity` | PASS | 1.000 | >= 99.00% valid references | 0 orphaned references across 0 checked |
| `null_rate` | FAIL | 0.000 | <= 5.00% nulls in any measured column | worst column null rate 1.000 |
| `freshness` | FAIL | 0.000 | <= 7 days since latest update | worst table age 1.000 days |
| `completeness` | FAIL | 0.250 | >= 1000 rows in every core table | 12 core tables below minimum row count |
| `consistency` | PASS | 1.000 | cross-table validations have zero orphaned references | 0 cross-table consistency violations |
| `pii_sanitization` | PASS | 1.000 | 0 PII findings in non-PII tables | 0 PII findings in non-PII tables |

## Alerts

- **P1** `null_rate`: null_rate failed: worst column null rate 1.000
- **P1** `freshness`: freshness failed: worst table age 1.000 days
- **P1** `completeness`: completeness failed: 12 core tables below minimum row count
