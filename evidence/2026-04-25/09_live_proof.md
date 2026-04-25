# LIVE EVIDENCE — 2026-04-25

## API Health (verified 07:33 UTC)
```
Status: healthy
Audit chain_valid: true
Audit chain_length: 382905
Database: healthy (SQLite, 5615 researchers, 12000 publications)
Qdrant: reachable, 19323 vectors indexed
```

## Login Test
```
Username: researcher_user
Password: researcher-pass
Result: SUCCESS - JWT issued with role=researcher, tier=1
```

## Query Test (Top 5 funding agencies)
```
Intent: structured
Routing: text_to_sql
SQL: SELECT gov_organisation_name, SUM(grant_received) AS total_grant
      FROM innovation_grant_from_govt
      GROUP BY gov_organisation_name ORDER BY total_grant DESC LIMIT 5
Results: 5 rows returned
  1. DST-SERB: 167500000
  2. DRDO: 124000000
  3. DBT: 22000000
  4. MeitY: 15000000
  5. AICTE: 3000000
Audit event logged: yes (audit_event_id present in response)
```

## Health Endpoints (both via proxy)
- Direct API: http://localhost:8000/health → healthy
- Frontend proxy: http://localhost:3000/health → healthy (same response)

## Test Suite Results
- Dhairya benchmark: 43/43 PASS in 23.95s
- Egress guard: 13/13 PASS
- Per-user audit binding: 26/26 PASS
- Chain integrity: 11/11 PASS
- Cost guard: 44/44 PASS
- Audit chain: VERIFIED PASSED (382,905 events, 0 errors)

## Backend Status
- API: running on port 8000
- Frontend: running on port 3000 (proxying to API)
- Qdrant: running on port 6333
- Database: SQLite (dev mode)
- Audit chain: valid, no corruption

## Tier Isolation Test
- Tier 1 (Researcher): full access to institution details
- Tier 2 (Government): aggregated stats only
- Tier 3 (Industry): anonymized, no PII exposure
(RBAC enforced at API middleware level, tested via unit tests)