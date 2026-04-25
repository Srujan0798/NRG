# Text-to-SQL Failure Pattern Ledger

This ledger captures rejected SQL patterns and the accepted replacement shape.

| Pattern | Rejected shape | Accepted shape |
| --- | --- | --- |
| Credit score parsing | `CAST(total_credit_score AS INTEGER)` | Parse `X:Y` components with `SPLIT_PART` or `SUBSTR` before numeric aggregation |
| Stage synonym leakage | `stage_of_technology = 'TRL 9'` | Expand to stored values such as `Level 9` or `Level 4` |
| Raw grant trend comparison | Row-by-row grant comparison | CTE grouped by institute and year, then self-join adjacent years |
| Ranked grant agencies | `SELECT DISTINCT ... ORDER BY ...` | `GROUP BY gov_organisation_name ORDER BY SUM(grant_received) DESC` |
| Grant and patent join | Join grants to patent rows without applicant text normalization | Match `combined_ipo_patent_data.applicants` to institute text with `lower(trim(...))` |
