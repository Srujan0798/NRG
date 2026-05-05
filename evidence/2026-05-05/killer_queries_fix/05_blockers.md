# Killer Queries Fix Blockers

Date: 2026-05-05

## Resolved In This Task

- KILLER-02 no longer falls into the bounded local fast path with no SQL.
- KILLER-03 no longer falls into the C4 funding read model.
- KILLER-02 SQL now includes `innovations_at_various_stages_of_technology_readiness_level`, `GROUP BY`, and `financial_year`.
- KILLER-03 SQL now includes `WITH`, `innovation_grant_from_govt`, `combined_ipo_patent_data`, and `HAVING`.
- Both KILLER-02 and KILLER-03 return at least one local seed row.

## Remaining Blockers

- Staging URL remains BLOCKED in `.claude/CURRENT_STATE.md`; this evidence is local TestClient/local seed evidence, not staging evidence.
- `bash scripts/run_critical_path_final.sh` reached healthy Postgres, Qdrant, Redis, and PgBouncer, but the bounded run did not complete the API/frontend image build before the timeout. See `00_stack_start.log`.
- External production gates remain out of scope for this task: staging smoke, cluster C4 with quotas enabled, founder GPG signatures, and credential rotation closure.

## Known Local Notes

- `03_latency.log` includes pytest pass/fail evidence plus appended P95 detail because the pytest test asserts P95 but does not print timing values by default.
- An authenticated SQL-sample extractor hit a transient SQLite refresh-token lock after repeated e2e calls; `04_sql_samples.json` was regenerated via the same killer-query fast-path function that `/query` uses after routing.
