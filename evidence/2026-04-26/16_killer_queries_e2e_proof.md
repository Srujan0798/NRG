# LB-3 Three Killer Queries Evidence

Timestamp: 2026-04-26T02:33:17+05:30

## Acceptance Trace

- [x] All three killer queries return cited rows through `/query`.
  - Evidence: `evidence/2026-04-26/killer_query_1_response.json`
  - Evidence: `evidence/2026-04-26/killer_query_2_response.json`
  - Evidence: `evidence/2026-04-26/killer_query_3_response.json`
- [x] p95 latency is under 4000ms over 20 researcher runs per query on the local volumetric proxy.
  - KILLER-01 p95: 9.78ms, row_count: 8, citation_count: 1
  - KILLER-02 p95: 9.79ms, row_count: 4, citation_count: 1
  - KILLER-03 p95: 8.69ms, row_count: 3, citation_count: 1
- [x] Row-floor is present locally.
  - `academic_courses_details`: 50000
  - `innovations_at_various_stages_of_technology_readiness_level`: 10000
  - `innovation_grant_from_govt`: 30000
  - `combined_ipo_patent_data`: 20000
  - `publications`: 100000
  - `researchers`: 5615
- [x] Plan logs are committed.
  - Evidence: `evidence/2026-04-26/explain_killer_1.txt`
  - Evidence: `evidence/2026-04-26/explain_killer_2.txt`
  - Evidence: `evidence/2026-04-26/explain_killer_3.txt`
- [x] Health endpoint returns valid JSON.
  - Endpoint snapshot: `evidence/2026-04-26/killer_query_health_endpoint.json`
  - Source snapshot: `evidence/2026-04-26/killer_query_health.json`
- [x] Regression gate passes.
  - Evidence: `evidence/2026-04-26/lb2_lb3_targeted_pytest.log`
  - Result: 123 passed in 7.48s

## Residual Gap

This workspace does not expose a reachable staging PostgreSQL `DATABASE_URL`, so the committed plan files are local SQLite volumetric proxy plans, not PostgreSQL `EXPLAIN ANALYZE`. The runner `scripts/capture_killer_query_evidence.py` will capture PostgreSQL `EXPLAIN ANALYZE` automatically when `DATABASE_URL` points to staging.
