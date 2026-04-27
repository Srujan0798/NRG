# LB-3 Killer Queries E2E Proof

Captured: 2026-04-27T11:44:42Z

Live API: `http://localhost:8000`

Dataset floor:
- `academic_courses_details`: 50,000 rows
- `innovations_at_various_stages_of_technology_readiness_level`: 50,000 rows
- `innovation_grant_from_govt`: 50,000 rows
- `combined_ipo_patent_data`: 50,000 rows
- `publications`: 50,000 rows
- `researchers`: 50,000 rows

Results:

| Query | Rows | Citations | P95 latency | Threshold | Evidence |
| --- | ---: | ---: | ---: | ---: | --- |
| KILLER-01 | 10 | 1 | 9.56 ms | 4000 ms | `killer_query_1_response.json`, `explain_killer_1.txt` |
| KILLER-02 | 10 | 1 | 10.2 ms | 4000 ms | `killer_query_2_response.json`, `explain_killer_2.txt` |
| KILLER-03 | 3 | 1 | 9.36 ms | 4000 ms | `killer_query_3_response.json`, `explain_killer_3.txt` |

Pytest proof:

`NRG_API_URL=http://localhost:8000 NRG_KILLER_QUERY_RUNS=5 pytest tests/e2e/test_three_killer_queries.py -q -m e2e --no-cov`

Result: `3 passed`.
