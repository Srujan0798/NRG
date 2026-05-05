# Deployment Runbook — NRG Staging → Production

**Date:** 2026-05-06
**Status:** BLOCKED — awaiting AWS/GCP credentials and cluster provisioning

---

## Prerequisites (Founder Must Provision)

Before any deployment step runs, the founder must have:

- [ ] **AWS Account** with admin IAM user or deploy role
- [ ] **ECR Registry** for nrg-api and nrg-frontend images (e.g., `123456789.dkr.ecr.ap-south-1.amazonaws.com/nrg`)
- [ ] **RDS PostgreSQL 16** instance (t3.medium, 100GB, multi-AZ)
- [ ] **EKS Cluster** (or ECS) with 3 worker nodes (m5.xlarge)
- [ ] **Redis ElastiCache** (cache.r6g.large)
- [ ] **Qdrant Cloud** or self-hosted on EKS (2GB RAM)
- [ ] **Domain registration** — nrg.gov.in (or staging.nrg.gov.in)
- [ ] **SSL Certificate** — via ACM or Let's Encrypt
- [ ] **Secrets Manager** — API keys, JWT secret, DB credentials

---

## Step 1: Build Containers Locally and Verify

### 1a. Build API image
```bash
docker build -t nrg-api:local -f Dockerfile.api .
docker run --rm nrg-api:local python -c "import src.api.main; print('API module OK')"
```

### 1b. Build Frontend image
```bash
cd frontend && npm ci && npm run build && cd ..
docker build -t nrg-frontend:local -f Dockerfile.frontend .
```

### Rollback: If build fails
- Check Python version matches 3.11
- Verify `pyproject.toml` is valid
- Check all required files (alembic.ini, src/, scripts/) are present

---

## Step 2: Push to Container Registry

### 2a. Tag images for ECR
```bash
AWS_ACCOUNT=123456789
REGION=ap-south-1
API_IMAGE=${AWS_ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com/nrg-api
FRONTEND_IMAGE=${AWS_ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com/nrg-frontend

docker tag nrg-api:local ${API_IMAGE}:latest
docker tag nrg-frontend:local ${FRONTEND_IMAGE}:latest

aws ecr get-login-password --region ${REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com

docker push ${API_IMAGE}:latest
docker push ${FRONTEND_IMAGE}:latest
```

### Rollback: If push fails
- Verify ECR repository exists: `aws ecr describe-repositories`
- Check IAM permissions for ECR push
- Retry with `--verbose`

---

## Step 3: Deploy to Staging

### 3a. Update Helm values for staging
```yaml
# infrastructure/helm/nrg/values.staging.yaml
api:
  image: ${API_IMAGE}:latest
  replicaCount: 2
  env:
    APP_ENV: staging
    DATABASE_URL: postgresql://user:pass@rds-endpoint:5432/nrg_staging
    QDRANT_HOST: qdrant-cluster.x.region.cloudprovider.com
    REDIS_URL: redis://cache-endpoint:6379/0

frontend:
  image: ${FRONTEND_IMAGE}:latest
  replicaCount: 2

ingress:
  host: staging.nrg.gov.in
  tls: true
```

### 3b. Deploy via Helm
```bash
helm upgrade --install nrg-staging infrastructure/helm/nrg \
  --namespace nrg-staging \
  --create-namespace \
  --values infrastructure/helm/nrg/values.staging.yaml \
  --wait --timeout 5m \
  --timeout 300s
```

### 3c. Verify pods are running
```bash
kubectl get pods -n nrg-staging
kubectl rollout status deployment/nrg-api -n nrg-staging
kubectl rollout status deployment/nrg-frontend -n nrg-staging
```

### Rollback: If deployment fails
```bash
kubectl rollout undo deployment/nrg-api -n nrg-staging
kubectl rollout undo deployment/nrg-frontend -n nrg-staging
helm rollback nrg-staging -n nrg-staging
```

---

## Step 4: Run Smoke Tests

### 4a. Basic health checks
```bash
STAGING_API=https://staging-api.nrg.gov.in

curl -fsS ${STAGING_API}/health \
  | jq '.status, .healthy'  # expect: "healthy", true

curl -fsS ${STAGING_API}/health/db \
  | jq '.ready, .dialect'  # expect: true, "postgresql"

curl -fsS ${STAGING_API}/health/qdrant \
  | jq '.ready, .collection_exists'  # expect: true, true

curl -fsS ${STAGING_API}/health/all \
  | jq '.status'  # expect: "healthy" or "degraded" (not "unhealthy")
```

### 4b. Smoke test query endpoint
```bash
curl -fsS -X POST ${STAGING_API}/api/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TEST_TOKEN" \
  -d '{"query": "top AI researchers by h-index"}' \
  | jq '.status, .sql_query'  # expect: "success", non-null SQL
```

### Rollback trigger: If any smoke test fails
```bash
helm rollback nrg-staging -n nrg-staging
kubectl rollout undo deployment/nrg-api -n nrg-staging
echo "REVERTED: Staging smoke tests failed — rolled back to previous release"
```

---

## Step 5: Run C4 Load Test Against Staging

### 5a. Run killer-query health check
```bash
curl -fsS https://staging-api.nrg.gov.in/api/health/killer_queries \
  | jq '.status, .queries[].latency_p99'
```

### 5b. Run Locust load test (from tests/load/)
```bash
cd tests/load
docker build -t nrg-locust -f Dockerfile.locust .

docker run --rm nrg-locust \
  --host staging-api.nrg.gov.in \
  --users 100 \
  --spawn-rate 10 \
  --run-time 5m \
  --headless
```

### 5c. Check P99 latency
```bash
kubectl top pods -n nrg-staging
kubectl logs -n nrg-staging -l app=nrg-api --tail=100 | grep "latency_p99"
```

### Rollback trigger: If P99 > 2000ms or error rate > 5%
```bash
helm rollback nrg-staging -n nrg-staging
```

---

## Step 6: Promote to Production (if staging passes)

### 6a. Manual approval gate
- Go to GitHub Actions → Deploy NRG workflow
- Click "Approve production deployment"
- Enter production environment secrets

### 6b. Update production Helm values
```bash
helm upgrade --install nrg-prod infrastructure/helm/nrg \
  --namespace nrg-production \
  --create-namespace \
  --values infrastructure/helm/nrg/values.prod.yaml \
  --wait --timeout 10m \
  --timeout 600s
```

### 6c. Run production smoke tests
```bash
PROD_API=https://api.nrg.gov.in

for endpoint in /health /health/db /health/qdrant /health/all; do
  STATUS=$(curl -fsS -o /dev/null -w "%{http_code}" ${PROD_API}${endpoint})
  if [ "$STATUS" != "200" ]; then
    echo "FAIL: ${PROD_API}${endpoint} returned $STATUS"
    exit 1
  fi
done
echo "All production health endpoints passed"
```

### Rollback: If production smoke fails
```bash
helm rollback nrg-prod -n nrg-production
kubectl rollout undo deployment/nrg-api -n nrg-production
```

---

## Deployment Checklist

- [ ] All tests passing in CI (deploy.yml test job green)
- [ ] Security scan complete (Trivy, Semgrep)
- [ ] Build succeeds (Dockerfile.api, Dockerfile.frontend)
- [ ] Images pushed to ECR
- [ ] Helm chart validated: `helm lint infrastructure/helm/nrg`
- [ ] Staging smoke tests pass (all /health/* endpoints)
- [ ] C4 load test P99 < 2000ms on staging
- [ ] Manual approval obtained for production
- [ ] Production smoke tests pass
- [ ] Stakeholders notified

---

## Rollback Quick Reference

| Step | Rollback Command |
|------|-----------------|
| Helm deploy | `helm rollback <release> -n <namespace>` |
| K8s deployment | `kubectl rollout undo deployment/<name> -n <namespace>` |
| ECR image | Re-tag previous image and re-push |
| Database migration | Run undo SQL script (must be versioned) |

---

## Key Files

| File | Purpose |
|------|---------|
| `infrastructure/helm/nrg/values.staging.yaml` | Staging Helm values |
| `infrastructure/helm/nrg/values.prod.yaml` | Production Helm values |
| `infrastructure/helm/nrg/templates/deployments/api-deployment.yaml` | API K8s deployment template |
| `.github/workflows/deploy.yml` | CI/CD pipeline |
| `docker-compose.prod.yml` | Production compose override |
| `scripts/sovereign_deploy.py` | Helm deployment script |