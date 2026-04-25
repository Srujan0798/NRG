# Deployment Pipeline Design Evidence

**Skill**: deployment-pipeline-design
**Applied**: Sat Apr 25 2026
**Evidence File**: `evidence/49_DEPLOYMENT_PIPELINE.md`

---

## Deployment Pipeline Design: NRG

### Overview

NRG uses Docker Compose for local deployment. For production, a Kubernetes-based pipeline would be appropriate.

---

## Current Pipeline

### Local (Docker Compose)

```yaml
# docker-compose.yml (existing)
services:
  api:
    build: ./Dockerfile.api
    ports:
      - "8000:8000"
  postgres:
    image: postgres:14
    ports:
      - "5432:5432"
  redis:
    image: redis
    ports:
      - "6379:6379"
  qdrant:
    image: qdrant/qdrant
    ports:
      - "6333:6333"
  frontend:
    build: ./Dockerfile.frontend
    ports:
      - "80:80"
```

**Issues**:
- nginx runs as root (CRITICAL)
- Internal ports exposed
- No health checks configured
- No rollback strategy

---

## Recommended Pipeline (Kubernetes)

### Stage Flow

```
┌─────────┐   ┌──────┐   ┌─────────┐   ┌────────┐   ┌──────────┐
│  Build  │ → │ Test │ → │ Staging │ → │Approve │ → │Production│
└─────────┘   └──────┘   └─────────┘   └────────┘   └──────────┘
```

### CI Stage (GitHub Actions)

```yaml
name: Deploy NRG

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build API
        run: docker build -f Dockerfile.api -t nrg-api:${{ github.sha }} .
      - name: Build Frontend
        run: docker build -f Dockerfile.frontend -t nrg-frontend:${{ github.sha }} .

  test:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Run unit tests
        run: pytest tests/unit/ -v
      - name: Security scan
        run: trivy image nrg-api:${{ github.sha }}

  deploy-staging:
    needs: test
    environment: staging
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to staging
        run: kubectl apply -f k8s/staging/

  integration-test:
    needs: deploy-staging
    runs-on: ubuntu-latest
    steps:
      - name: E2E tests
        run: pytest tests/e2e/ -v

  deploy-production:
    needs: integration-test
    environment: production
    runs-on: ubuntu-latest
    steps:
      - name: Canary deploy (10%)
        run: kubectl argo rollouts promote nrg-api --to-weight=10
      - name: Wait 5 minutes
        run: sleep 300
      - name: Promote to 100%
        run: kubectl argo rollouts promote nrg-api

  verify:
    needs: deploy-production
    runs-on: ubuntu-latest
    steps:
      - name: Health check
        run: curl -sf https://api.nrg.example.com/health
```

---

## Deployment Strategies

### Current State: Rolling (Docker Compose)

No strategy — simple docker-compose up.

### Recommended: Canary (Kubernetes)

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: nrg-api
spec:
  replicas: 10
  strategy:
    canary:
      steps:
        - setWeight: 10
        - pause: { duration: 5m }
        - setWeight: 50
        - pause: { duration: 5m }
        - setWeight: 100
```

---

## Health Checks

### Current: None

### Recommended (API)

```python
@app.get("/health/ready")
async def readiness():
    db_ok = await check_db()
    redis_ok = await check_redis()
    status = "ok" if db_ok and redis_ok else "degraded"
    code = 200 if status == "ok" else 503
    return JSONResponse({"status": status}, status_code=code)
```

---

## Rollback

### Automated

```yaml
- name: Rollback on failure
  if: failure()
  run: kubectl argo rollouts abort nrg-api
```

### Manual

```bash
kubectl argo rollouts undo nrg-api
```

---

## Issues with Current Pipeline

| Issue | Severity | Fix |
|-------|----------|-----|
| No CI/CD | 🔴 CRITICAL | Implement GitHub Actions |
| nginx as root | 🔴 CRITICAL | Add USER nginx |
| No health checks | 🟡 MEDIUM | Add /health/ready endpoint |
| No rollback | 🟡 MEDIUM | Implement Argo Rollouts |
| Internal ports exposed | 🟡 MEDIUM | Remove port mappings |
| No canary strategy | 🟡 MEDIUM | Implement Argo Rollouts |
| Full suite times out | 🟡 MEDIUM | pytest-xdist parallelization |

---

## DORA Metrics for NRG

| Metric | Target | Current |
|--------|--------|---------|
| Deployment Frequency | Multiple/day | Manual |
| Lead Time for Changes | < 1 hour | Unknown |
| Change Failure Rate | < 5% | Unknown |
| MTTR | < 1 hour | Unknown |

---

## Skill Deliverable

**Status**: COMPLETED

Deployment pipeline design for NRG:
- Current: Docker Compose (no CI/CD)
- Recommended: GitHub Actions + Kubernetes with canary deploys
- 7 issues identified with current pipeline
- Argo Rollouts recommended for progressive delivery
