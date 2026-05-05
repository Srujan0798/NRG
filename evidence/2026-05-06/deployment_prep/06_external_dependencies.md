# External Dependencies — What Founder Must Provision

**Date:** 2026-05-06
**Priority:** CRITICAL — all are blockers for production deployment

---

## Cloud Infrastructure (AWS)

| Dependency | Type | Spec | Purpose |
|------------|------|------|---------|
| AWS Account + IAM Role | Account | Admin or DeployAdmin policy | Container registry, EKS, RDS |
| ECR Registry (nrg-api) | Registry | private, region ap-south-1 | API container storage |
| ECR Registry (nrg-frontend) | Registry | private, region ap-south-1 | Frontend container storage |
| EKS Cluster | Compute | 3x m5.xlarge, Kubernetes 1.29 | Production K8s cluster |
| RDS PostgreSQL 16 | Database | t3.medium, multi-AZ, 100GB, encrypted | Primary database |
| ElastiCache Redis | Cache | r6g.large, cluster mode | Query result caching |
| ACM SSL Certificate | Security | *.nrg.gov.in | HTTPS/TLS |
| Route 53 Hosted Zone | DNS | nrg.gov.in | Domain management |
| Secrets Manager | Security | API key, JWT secret, DB credentials | Secret rotation |

---

## External Services

| Service | Provider | Purpose | Alternatives |
|---------|----------|---------|---------------|
| Qdrant Vector Store | Qdrant Cloud | Semantic search, embeddings | Self-hosted on EKS |
| LLM Provider (Gemini/OpenAI) | Google/OpenAI | AI synthesis fallback | Local llama.cpp |
| Domain Registration | NIC/Registrar | nrg.gov.in | staging.nrg.gov.in |

---

## NRG-Specific Infrastructure

| Component | Config Path | Notes |
|-----------|-------------|-------|
| Kong API Gateway | `infrastructure/kong/` | Can be K8s ingress or sidecar |
| Helm Chart | `infrastructure/helm/nrg/` | Primary deployment mechanism |
| nginx reverse proxy | `infrastructure/nginx/` | SSL termination, static file serve |

---

## GitHub Secrets Required

| Secret | Used In | Format |
|--------|---------|--------|
| `AWS_ACCESS_KEY_ID` | deploy.yml | AWS credentials |
| `AWS_SECRET_ACCESS_KEY` | deploy.yml | AWS credentials |
| `JWT_SECRET` | api env | min 32 bytes, HS256 |
| `APPROVAL_SECRET` | deploy.yml | Manual approval gate |
| `PRODUCTION_APPROVERS` | deploy.yml | GitHub usernames |
| `DLP_TOKENIZATION_SECRET` | Kong | min 32 bytes |

---

## Environment Variables for Helm

| Variable | Example Value | Source |
|----------|--------------|--------|
| `DATABASE_URL` | postgresql://user:pass@host:5432/nrg | AWS Secrets Manager |
| `QDRANT_HOST` | qdrant.x.cloudprovider.com | Qdrant Cloud |
| `QDRANT_PORT` | 6333 | Qdrant Cloud |
| `REDIS_URL` | redis://cache.x.region.amazon.com:6379/0 | ElastiCache |
| `POSTGRES_PASSWORD` | (from Secrets Manager) | RDS |
| `GEMINI_API_KEY` | (from Secrets Manager) | LLM provider |
| `OPENAI_API_KEY` | (from Secrets Manager) | LLM provider |

---

## One-Time Setup Order

1. Register domain (nrg.gov.in) via NIC
2. Create AWS account + IAM deploy role
3. Create ECR repositories (nrg-api, nrg-frontend)
4. Provision EKS cluster (3x m5.xlarge)
5. Provision RDS PostgreSQL (t3.medium, multi-AZ)
6. Provision ElastiCache Redis (r6g.large)
7. Set up Qdrant Cloud cluster
8. Request ACM SSL certificate for *.nrg.gov.in
9. Create Route 53 hosted zone + DNS records
10. Add GitHub secrets for CI/CD
11. Configure GitHub Environment protections (staging, production)
12. Add `PRODUCTION_APPROVERS` GitHub variable

---

## Estimated Provisioning Time

- AWS account + IAM: 1 day
- EKS cluster: 2 hours
- RDS PostgreSQL: 1 hour
- ElastiCache: 30 minutes
- Qdrant Cloud: 30 minutes
- ACM SSL: 15 minutes (after domain)
- Route 53 + DNS: 1 hour
- GitHub secrets: 15 minutes

**Total: ~1 day with all info available**