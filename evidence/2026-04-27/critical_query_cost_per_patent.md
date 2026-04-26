# Critical Production Query Evidence — Cost Per Granted Patent

**Date:** 2026-04-27
**Scope:** Local production-query hardening for the requested critical query:

> Calculate the cost per patent granted for institutes with >₹10Cr grants.

## What Changed

- Promoted the cost-per-granted-patent question into the bounded API query path in `src/api/main.py`.
- Preserved the `>₹10Cr` grant threshold as `HAVING SUM(grant_received) > 100000000`.
- Used `combined_ipo_patent_data` with `status = 'Granted'`.
- Joined patent applicants to grant institutes through `combined_ipo_patent_data.applicants`.
- Sorted with `ORDER BY cost_per_patent IS NULL, cost_per_patent ASC` so institutes with no granted patents do not appear above valid ratios.
- Mirrored the same semantics in the Text-to-SQL fallback path in `src/skills/text_to_sql/skill.py`.

## Regression Evidence

Command:

```bash
.venv/bin/pytest \
  tests/benchmarks/test_dhairya_adversarial.py \
  tests/api/test_langgraph_api.py::test_fast_topic_matches_renewable_publication_control_query \
  tests/api/test_langgraph_api.py::test_fast_query_release_seed_fallback_covers_audit_walkthrough \
  tests/api/test_langgraph_api.py::test_cost_per_patent_critical_query_uses_bounded_sql_path \
  tests/api/test_langgraph_api.py::test_release_seed_graph_covers_hydrogen_visualization \
  -q
```

Result:

- Evidence log: `evidence/2026-04-27/critical_query_regression.log`
- Summary: `78 passed in 4.84s`

## Local Data Evidence

Query result snapshot:

- Evidence CSV: `evidence/2026-04-27/cost_per_patent_10cr_results.csv`

Top rows from the local reference database:

| institute | total_grant | granted_patents | cost_per_patent |
|---|---:|---:|---:|
| IIT Gandhinagar | 31,466,300,000 | 2,499 | 12,591,556.62 |
| IIT Kharagpur | 31,472,250,000 | 2,499 | 12,593,937.58 |
| IIT Roorkee | 31,478,200,000 | 2,499 | 12,596,318.53 |
| IIT Hyderabad | 31,482,225,000 | 2,499 | 12,597,929.17 |
| IIT Delhi | 38,983,475,000 | 2,499 | 15,599,629.85 |

## Remaining External Gates

This evidence is local and uses the existing reference SQLite database. It does not replace:

- PostgreSQL `EXPLAIN ANALYZE` on the target deployment database.
- The official 600GB data ingest.
- Sovereign-cluster C4 load acceptance.
