# Qdrant/Redis Local Health Restoration

Date: 2026-05-02

## Scope

Restore the local live-service health gate for Qdrant and Redis. This is local
proof only; it does not replace deployed or cluster evidence.

## Commands

```bash
colima start
docker compose up -d qdrant redis
curl -fsS http://127.0.0.1:6333/healthz
docker exec nrg-redis redis-cli ping
QDRANT_HOST=127.0.0.1 QDRANT_PORT=6333 REDIS_URL=redis://127.0.0.1:6379/0 \
  .venv/bin/python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000
curl -fsS http://127.0.0.1:8000/health/all
curl -fsS http://127.0.0.1:8000/health/qdrant
curl -fsS http://127.0.0.1:8000/api/vectors/health
```

## Evidence

| Gate | Status | Evidence |
| --- | --- | --- |
| Colima runtime | PASS | `62_colima_start.log` |
| Compose services | PASS | `63_compose_qdrant_redis_up.log` |
| Qdrant direct health | PASS | `curl /healthz` returned `healthz check passed` |
| Redis direct health | PASS | `redis-cli ping` returned `PONG` |
| API `/health/all` | PASS | `64_live_health_all_after_services.json` |
| API `/health/qdrant` | PASS | `65_live_health_qdrant_after_services.json` |
| API `/api/vectors/health` | PASS | `66_live_vectors_health_after_services.json` |
| Colima stack `/health/all` | PASS | `74_colima_stack_health_all.json` |

## Result

Local `/health/all` is healthy with Qdrant and Redis running. Qdrant exposes the
`nrg_research` collection; vector health reports 1,800 vectors, dimension 1024,
COSINE distance, and green index status.

## Boundaries

- The host uvicorn process was stopped after evidence capture; no host process
  is listening on port 8000 in the final verification log.
- Colima remains running. Because the existing Compose services use
  `restart: unless-stopped`, the Colima-side `nrg-api`, `nrg-frontend`,
  `nrg-postgres`, `nrg-pgbouncer`, `nrg-qdrant`, and `nrg-redis` containers are
  running and healthy in `72_colima_docker_ps.log`.
- Host Docker socket/port forwarding was inconsistent after startup, so final
  service persistence was verified with `colima ssh -- docker ps` plus
  Colima-internal Qdrant/Redis probes.
- External/deployed Qdrant, Redis, browser replay, cluster C4, and founder
  signing remain separate gates.
