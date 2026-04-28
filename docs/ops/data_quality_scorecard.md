# Data Quality Scorecard

- Generated: `2026-04-28T12:38:02.916960+00:00`
- Database: `sqlite:///nrg_research.db`
- Overall: `FAIL` (0.571)

| Pillar | Status | Score | Threshold | Detail |
| --- | --- | ---: | --- | --- |
| `schema_coverage` | FAIL | 0.000 | >= 58 expected tables present | 0/58 expected tables present |
| `referential_integrity` | PASS | 1.000 | >= 99.00% valid references | 0 orphaned references across 0 checked |
| `null_rate` | FAIL | 0.000 | <= 5.00% nulls in any measured column | worst column null rate 1.000 |
| `freshness` | PASS | 0.996 | <= 7 days since latest update | worst table age 0.031 days |
| `completeness` | FAIL | 0.000 | >= 1000 rows in every core table | 16 core tables below minimum row count |
| `consistency` | PASS | 1.000 | cross-table validations have zero orphaned references | 0 cross-table consistency violations |
| `pii_sanitization` | PASS | 1.000 | 0 PII findings in non-PII tables | 0 PII findings in non-PII tables |

## Alerts

- **P1** `schema_coverage`: schema_coverage failed: 0/58 expected tables present
- **P1** `null_rate`: null_rate failed: worst column null rate 1.000
- **P1** `completeness`: completeness failed: 16 core tables below minimum row count
