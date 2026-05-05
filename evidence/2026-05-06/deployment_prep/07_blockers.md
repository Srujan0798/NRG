# Blockers — Deployment Gate Preparation

**Date:** 2026-05-06
**Status:** BLOCKED

---

## Critical Blockers (Cannot Deploy Without)

| Blocker | Description | Action Required |
|---------|-------------|-----------------|
| **AWS Credentials** | No AWS access key/secret configured in GitHub | Founder: Add `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` to GitHub secrets |
| **Cloud Cluster** | EKS cluster not provisioned; deploy.yml has placeholder kubectl commands | Founder: Provision EKS cluster, update deploy.yml with real cluster context |
| **ECR Registry** | Images built but no ECR push target; currently only ghcr.io | Founder: Create ECR repos, update image tags in deploy.yml |
| **JWT_SECRET** | deploy.yml:25 has hardcoded CI placeholder `ci-jwt-secret-for-deploy-workflow-2026-minimum-32-bytes` | Replace with `{{ secrets.JWT_SECRET }}` before production |

---

## High Priority (Must Fix Before Production)

| Issue | Description | Action Required |
|-------|-------------|-----------------|
| **Production database** | deploy.yml:21-22 uses SQLite (`sqlite:///data/nrg_research.db`) | Replace with RDS PostgreSQL connection string |
| **Placeholder deployment** | deploy.yml:212, 253 have `echo DEPLOYMENT_COMMANDS_WOULD_GO_HERE` | Replace with real Helm/kubectl commands after cluster provisioning |
| **Placeholder smoke tests** | deploy.yml:216-217, 258 have commented curl commands | Uncomment and point to real staging/prod URLs after DNS provisioning |
| **Frontend build timeout** | Dockerfile.frontend takes >5 min (npm ci + build inside Docker) | Pre-build dist/ and copy into nginx, or use multi-stage caching |
| **Kong bootstrap localhost** | infrastructure/kong/bootstrap.py:167-168 has hardcoded localhost:8004, localhost:8000 | Make configurable via environment variables |

---

## Medium Priority (Nice to Have)

| Issue | Description | Action Required |
|-------|-------------|-----------------|
| **No Argo Rollouts** | Current deploy is rolling update; no canary/blue-green | Consider Argo Rollouts for safer production promotion |
| **No automated rollback** | Pipeline has no metric-based rollback trigger | Add Prometheus-based rollback on error rate > 1% |
| **No secrets rotation** | Secrets stored in GitHub secrets; no rotation schedule | Move to AWS Secrets Manager with rotation |

---

## Files Changed

```
evidence/2026-05-06/deployment_prep/00_summary.md
evidence/2026-05-06/deployment_prep/01_api_docker_build.log
evidence/2026-05-06/deployment_prep/02_hardcoded_paths.log
evidence/2026-05-06/deployment_prep/03_unparameterized_secrets.log
evidence/2026-05-06/deployment_prep/04_health_endpoints.log
evidence/2026-05-06/deployment_prep/05_deployment_runbook.md
evidence/2026-05-06/deployment_prep/06_external_dependencies.md
evidence/2026-05-06/deployment_prep/07_blockers.md
```

---

## Next Steps

1. Founder provisions AWS infrastructure (ECR, EKS, RDS, ElastiCache, Qdrant Cloud)
2. Founder adds GitHub secrets (AWS credentials, JWT secret)
3. Update deploy.yml with real Helm/kubectl deployment commands
4. Replace SQLite DATABASE_URL in deploy.yml with RDS PostgreSQL
5. Provision DNS records (staging.nrg.gov.in, nrg.gov.in)
6. Run end-to-end smoke tests against staging
7. Run C4 load test
8. Promote to production with manual approval gate