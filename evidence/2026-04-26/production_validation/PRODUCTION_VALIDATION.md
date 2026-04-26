# NRG Local Production Validation Evidence

**Date:** 2026-04-26
**Validated By:** Principal engineering pass
**Status:** Local handoff-ready, external sovereign-cluster gates pending

## Executive Summary

The local NRG release is ready for professor-assistant technical evaluation. The API contract, tier response filtering, critical query paths, schema parity, audit evidence, frontend build, and live red-team replay have reproducible local evidence.

This file is intentionally precise: the system is not yet signed off for sovereign-cluster production operation because three external gates still require the target infrastructure and official dataset.

## External Gates Not Closed Locally

| Gate | Current State | Required Evidence |
|---|---|---|
| C4 1000-user SLO | Pending | Load run on sovereign Kubernetes with representative data and P99 evidence. |
| C5 vector-drift baseline | Pending | Qdrant baseline on production corpus and scheduled drift check. |
| Official 600GB ingest | Pending | Signed intake run, row-count reconciliation, and query validation on the real dataset. |

## Evidence Files

| Evidence | Result |
|---|---|
| `../test_suite_full.log` | 1572 passed, 63 skipped, 219 deselected in 250.34s. |
| `../37_live_red_team_replay_chunked.md` | 0 dangerous allowed responses in chunked live API replay. |
| `../killer_query_health.json` | Three critical queries healthy with P95 under 60ms locally. |
| `../schema_parity_58_58.txt` | 58/58 schema parity and active Alembic head recorded. |
| `../explain_index_usage.txt` | Local query-plan and index-path evidence captured. |
| `tier_differentiation_live.json` | Tier response filtering evidence captured. |

## API Contract

The production `/query` response must expose enough transparency for review and enough filtering for privacy:

```json
{
  "audit_event_id": "03214dbd1c2d1dd79789e24a258c7e7b58a701bfc93ee38073",
  "sql_query": "SELECT COUNT(*) AS count FROM publications WHERE publications.access_tier >= 1 LIMIT 100",
  "sql_results": [{"count": 50000}],
  "sql_queries": [],
  "response": "There are 50,000 publications in the database.",
  "status": "success",
  "tier": 1
}
```

## Tier Isolation

Tier 3 responses were checked at the API boundary. The acceptance condition is that restricted users do not receive raw PII keys or values in the JSON payload, regardless of what the frontend renders.

| PII Type | Tier 3 Exposure |
|---|---:|
| Email | No |
| Phone | No |
| Aadhaar | No |
| PAN | No |

## Critical Query Health

Local critical query health is recorded in `../killer_query_health.json`:

| Query | Local P95 | Rows |
|---|---:|---:|
| KILLER-01 | 25.04 ms | 8 |
| KILLER-02 | 52.95 ms | 4 |
| KILLER-03 | 22.80 ms | 3 |

These timings are local-reference timings. They are not a substitute for the C4 sovereign-cluster SLO run.

## Audit Chain

Audit-chain verification evidence is recorded in the 2026-04-26 evidence directory. The acceptance condition is that `verify_chain()` returns a valid chain with zero hash mismatches before handoff.

## Security Replay

The chunked live API security replay completed with no dangerous allowed responses:

| Classification | Count |
|---|---:|
| BLOCKED | 192 |
| DOWNGRADED | 12 |
| ALLOWED-SAFE | 6 |
| ALLOWED-DANGEROUS | 0 |

## Acceptance Position

| Criterion | Local Status |
|---|---:|
| `docker compose config` validates | Pass |
| API returns transparent query metadata | Pass |
| Tier 3 PII filtering at API layer | Pass |
| 58-table schema parity | Pass |
| Critical local queries under 4 seconds | Pass |
| Frontend production build | Pass |
| C4 1000-user sovereign-cluster SLO | Pending external run |
| C5 production vector-drift baseline | Pending external run |
| Official 600GB data validation | Pending external run |

## Conclusion

**Overall local readiness:** 8 / 10
**Professor-assistant technical evaluation:** Ready locally
**Sovereign-cluster production sign-off:** Not complete until C4, C5, and official 600GB ingest evidence are attached

The largest remaining risk is not the local app path. It is unverified behavior on the official data volume and target cluster. Do not remove that caveat from the handoff package until the external runs are complete.
