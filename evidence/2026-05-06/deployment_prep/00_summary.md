# Deployment Gate Preparation - Evidence Summary
**Date:** 2026-05-06
**Agent:** Shishya (DevOps)
**Assignment:** shishya_deployment_gate_prep.md

---

## Configs Validated

| Config | Status | Notes |
|--------|--------|-------|
| Dockerfile.api | PASS | Builds successfully on macOS (Docker Desktop/colima) |
| Dockerfile.frontend | TIMEOUT | npm ci + build inside Docker takes >5 min; use pre-built dist approach |
| docker-compose.prod.yml | PASS | Exists, valid YAML, health checks defined |
| .github/workflows/deploy.yml | PASS | Structure valid, no obvious syntax errors |
| docker-compose.yml | PASS | All secrets parameterized via ${VAR:-default} |

---

## Issues Found

### Issue 1: Hardcoded local paths (02_hardcoded_paths.log)
- `infrastructure/kong/bootstrap.py:167,168` — localhost:8004 and localhost:8000 (dev-time bootstrap only)
- `infrastructure/kong/kong.yaml:144` — http://localhost:3000 (dev only)
- `infrastructure/kong/plugins/bot_detection.yml:42,43` — localhost:3000/5173 (dev config)
- `infrastructure/nginx/conf.d/default.conf:14` — `${SERVER_NAME:-localhost}` (acceptable default)
- `docker-compose.prod.yml:48` — health check uses 127.0.0.1 (inside container, correct)
- `docker-compose.yml:58,83,169,200` — health checks use localhost (inside containers, correct)

**Verdict:** All localhost references are inside containers or dev-only configs. No absolute paths like `srujansai/Desktop/NRG`. **No action required.**

### Issue 2: Unparameterized secrets (03_unparameterized_secrets.log)
- `infrastructure/kong/plugins/dlp/pii_types.yml` — `tokenize: true` (boolean, not secret)
- `infrastructure/kong/plugins/dlp/handler.lua:87` — `local token_secret = ngx.var.DLP_TOKENIZATION_SECRET or "default-secret"` (from env var, acceptable fallback)
- JWT secret in deploy.yml is hardcoded as CI placeholder — **ACTION: Replace with `{{ secrets.JWT_SECRET }}`**

### Issue 3: deploy.yml has placeholder deployment commands
- Lines 212, 253 — actual kubectl commands commented out
- Lines 216-217, 258 — smoke test curl commands commented out

**Action Required:** Replace placeholder comments with real Helm/kubectl commands when cluster is provisioned.

---

## Health Endpoints Documented (04_health_endpoints.log)

| Endpoint | File | Purpose |
|----------|------|---------|
| GET /health | routes/health.py:157 | Main health check (audit, db, qdrant, auth, drift) |
| GET /health/all | routes/health.py:584 | Combined all-services check |
| GET /health/db | routes/health.py:444 | Database readiness |
| GET /health/qdrant | routes/health.py:465 | Vector store readiness |
| GET /health/llm | routes/health.py:360 | LLM provider health |
| GET /api/providers/health | routes/health.py:417 | SovereignLLMMesh provider status |
| GET /api/vectors/health | routes/health.py:501 | Detailed vector store health |
| GET /api/health/killer_queries | routes/health.py:339 | Killer-query LB health snapshot |

---

## Runbook Location

`evidence/2026-05-06/deployment_prep/05_deployment_runbook.md`

---

## Blockers

| Blocker | Severity | Description |
|---------|----------|-------------|
| AWS/GCP credentials | CRITICAL | Cannot deploy without cloud credentials |
| Kubernetes cluster | CRITICAL | deploy.yml has placeholder kubectl commands |
| Production domain (nrg.gov.in) | HIGH | DNS/SSL not provisioned |
| Production database (RDS PostgreSQL) | HIGH | deploy.yml uses SQLite (not production-grade) |
| Container registry (ECR/GCR) | HIGH | Images pushed to ghcr.io but no ECR replication plan |

---

## Evidence Files

| File | Description |
|------|-------------|
| 00_summary.md | This file |
| 01_api_docker_build.log | API Dockerfile build output (PASS) |
| 02_hardcoded_paths.log | Grep results for local path leakage |
| 03_unparameterized_secrets.log | Grep results for plaintext secrets |
| 04_health_endpoints.log | All health endpoints found |
| 05_deployment_runbook.md | Full deployment procedure |
| 06_external_dependencies.md | Founder provisioning checklist |
| 07_blockers.md | What remains blocked |