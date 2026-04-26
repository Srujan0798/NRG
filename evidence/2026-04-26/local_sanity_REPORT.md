# NRG Local Sanity Report

Date: 2026-04-26
Host: founder laptop local stack
Commit range observed: 006354e, 20ba595 plus dirty working tree

## Stack State

- PostgreSQL container: healthy on 127.0.0.1:5432.
- Redis container: healthy on 127.0.0.1:6379.
- Qdrant container: healthy on 127.0.0.1:6333.
- API: serving locally through `.venv/bin/uvicorn` on 127.0.0.1:8000.
- Containerized API image: not sealed. Docker Buildx and legacy builder both stalled on the large ML runtime image path.
- Frontend container: not sealed in this pass because the combined image build was stopped after the API build path wedged.

## Changes Made In This Pass

- Added `.dockerignore` to keep local artifacts out of Docker build context.
- Reduced frontend build context from roughly 785 MB to roughly 2 MB.
- Reduced API build context to KB-scale source context.
- Updated `Dockerfile.api` so the runtime stage reuses the dependency-built stage and still runs as a non-root user.

## Health Checks

`GET /health`: PASS

- Status: healthy
- Database dialect: postgresql
- Researchers: 50,000
- Publications: 50,000
- Audit deep check: skipped by fast readiness mode

`GET /health/all`: DEGRADED

- API: healthy
- Qdrant: healthy, collections empty
- Redis: healthy
- Consent service: operational
- Local LLM: unhealthy, connection refused

Startup note: API embedding warm-up completed in 86.7 seconds and made external Hugging Face requests for model resolution.

## Focused Test Result

Command:

```bash
.venv/bin/python -m pytest tests/auth/test_jwt_handler.py tests/api/test_tier_isolation_live.py -q --tb=short
```

Result: PASS, 8 passed in 26.90 seconds.

Known test hygiene issue: coverage emitted warnings from an existing corrupted `.coverage` file. Coverage artifacts were not treated as sealable evidence.

## Canonical Query Evidence

| Role | Query | HTTP | Elapsed ms | Rows | Citations | Confidence | Evidence |
|---|---:|---:|---:|---:|---:|---|---|
| T1 Researcher | 01 | 200 | 17.95 | 10 | 1 | high | evidence/2026-04-26/local_sanity_t1_researcher_killer-01.json |
| T1 Researcher | 02 | 200 | 140.11 | 10 | 1 | high | evidence/2026-04-26/local_sanity_t1_researcher_killer-02.json |
| T1 Researcher | 03 | 200 | 886.10 | 3 | 1 | high | evidence/2026-04-26/local_sanity_t1_researcher_killer-03.json |
| T2 Government | 01 | 200 | 65.76 | 10 | 1 | high | evidence/2026-04-26/local_sanity_t2_government_killer-01.json |
| T2 Government | 02 | 200 | 65.99 | 10 | 1 | high | evidence/2026-04-26/local_sanity_t2_government_killer-02.json |
| T2 Government | 03 | 200 | 92.65 | 3 | 1 | high | evidence/2026-04-26/local_sanity_t2_government_killer-03.json |
| T3 Industry | 01 | 200 | 93.76 | 10 | 1 | high | evidence/2026-04-26/local_sanity_t3_industry_killer-01.json |
| T3 Industry | 02 | 200 | 72.89 | 10 | 1 | high | evidence/2026-04-26/local_sanity_t3_industry_killer-02.json |
| T3 Industry | 03 | 200 | 116.03 | 3 | 1 | high | evidence/2026-04-26/local_sanity_t3_industry_killer-03.json |

## Tier-Shape Proof

| Query | T1-only keys | T3-only keys | Verdict |
|---|---:|---:|---|
| 01 | 5 | 6 | PASS |
| 02 | 4 | 6 | PASS |
| 03 | 5 | 6 | PASS |

The same question produces visibly different response shapes between T1 and T3.

## Serious Open Blockers

1. Container image build is not sealed on this laptop. Build context is fixed, but API image export/build still stalls on the ML runtime path.
2. `/health/all` is degraded because the local LLM endpoint is not running.
3. Qdrant is healthy but has no collections in this local run.
4. API startup takes 86.7 seconds and reaches external model hosts during warm-up.
5. The working tree contains unrelated dirty frontend/evidence artifacts that were not created in this pass and were not committed.

## Verdict

FIXED-AND-VERIFIED locally:

- Development password alias boot blocker is fixed in commit `20ba595`.
- Docker build context bloat is fixed in the working tree via `.dockerignore`.
- Local API path is healthy on uvicorn.
- Focused auth and tier-shape tests pass.
- Three canonical user-acceptance queries return cited rows for all three tiers.

NOT COMPLETE:

- Full project completion cannot be claimed until containerized API/frontend build, local LLM health, Qdrant collection readiness, full test suite, frontend click-through, and cluster-bound production gates are sealed with evidence.
