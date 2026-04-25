# PRODUCTION READINESS — NRG National Research Graph

**Date:** 2026-04-25  
**Status:** STOP ALL DEMO WORK. THIS IS A REAL PRODUCT.  
**Target:** Production deployment on Indian infrastructure

---

## ❌ WHAT WE STOP DOING

| Demo Work | Why It Stops |
|-----------|-------------|
| Demo scripts | No scripts. Real users will use this. |
| Screenshot polish for presentations | UI must work, not just look good in screenshots |
| Hardcoded demo credentials | Production auth only |
| "Works on my laptop" testing | Must work on bare metal / VMs |
| SQLite for everything | Production database required |
| Single-process uvicorn | Must handle concurrent users |
| No HTTPS | TLS mandatory |
| Debug mode | Production logging only |

---

## ✅ PRODUCTION MILESTONES

### Milestone 1: Infrastructure (Week 1)
**Goal:** NRG runs on a real server, not a MacBook.

| Task | Owner | Acceptance Criteria |
|------|-------|---------------------|
| 1.1 Provision server | DevOps | Bare metal or VM in Indian data center (not AWS/GCP/Azure) |
| 1.2 Dockerize backend | Backend | `docker build -t nrg-api .` produces working image |
| 1.3 Dockerize frontend | Frontend | `docker build -t nrg-frontend .` produces working image |
| 1.4 Docker Compose | DevOps | `docker-compose up` starts full stack (API + frontend + PostgreSQL + Qdrant + Redis) |
| 1.5 Reverse proxy | DevOps | Nginx serves frontend and routes `/api` to backend |
| 1.6 SSL/TLS | DevOps | Let's Encrypt certificates, HTTPS only, HTTP→HTTPS redirect |
| 1.7 Domain + DNS | DevOps | `nrg.iitgn.ac.in` or similar points to server |

### Milestone 2: Database (Week 1-2)
**Goal:** Move from SQLite to PostgreSQL. No data loss.

| Task | Owner | Acceptance Criteria |
|------|-------|---------------------|
| 2.1 PostgreSQL setup | Backend | PostgreSQL 15+ running, users created, backups configured |
| 2.2 Schema migration | Backend | All 12 tables created via Alembic migrations |
| 2.3 Data migration | Backend | All 5,615 researchers + 12,000 publications migrated from SQLite |
| 2.4 Connection pooling | Backend | SQLAlchemy pool_size=20, max_overflow=40 |
| 2.5 Backup strategy | DevOps | Daily automated backups to S3-compatible storage |
| 2.6 Restore tested | DevOps | Full restore from backup tested and documented |

### Milestone 3: Authentication (Week 2)
**Goal:** Real users, real auth, no hardcoded passwords.

| Task | Owner | Acceptance Criteria |
|------|-------|---------------------|
| 3.1 Remove demo credentials | Security | No "researcher-pass" / "government-pass" in codebase or env |
| 3.2 Institutional SSO | Backend | SAML/OAuth2 integration with IIT GN auth system |
| 3.3 Government tier IP allowlist | Security | Configurable IP ranges, enforced at middleware |
| 3.4 Password policy | Security | Min 12 chars, complexity requirements, rotation |
| 3.5 Session management | Security | JWT refresh tokens, secure cookies, HttpOnly, SameSite |
| 3.6 Account provisioning | Backend | Admin UI to create/disable accounts |

### Milestone 4: Security Hardening (Week 2-3)
**Goal:** OWASP Top 10 covered. Audit-ready.

| Task | Owner | Acceptance Criteria |
|------|-------|---------------------|
| 4.1 Remove debug endpoints | Security | No `/debug`, `/docs` in production (or auth-protected) |
| 4.2 CORS lockdown | Security | Only allow origin from configured domain |
| 4.3 Rate limiting | Security | Per-IP + per-user rate limits, configurable per tier |
| 4.4 Input sanitization | Security | SQL injection tested, XSS tested, command injection tested |
| 4.5 Secrets management | Security | No API keys in code. Use HashiCorp Vault or env files with strict perms |
| 4.6 Dependency audit | Security | `pip-audit` and `npm audit` pass with zero critical/high |
| 4.7 Container hardening | Security | Non-root user, read-only filesystem, minimal base image |
| 4.8 Network policies | Security | Internal services (Qdrant, Redis) not exposed externally |

### Milestone 5: Performance (Week 3)
**Goal:** Handle 100 concurrent users, <2s response time.

| Task | Owner | Acceptance Criteria |
|------|-------|---------------------|
| 5.1 Redis caching | Backend | Query results cached, cache invalidation on data update |
| 5.2 Uvicorn workers | Backend | `gunicorn` with 4+ uvicorn workers, not single process |
| 5.3 Async database | Backend | `asyncpg` driver, async SQLAlchemy sessions |
| 5.4 Qdrant persistence | Backend | Named volume, not anonymous. Survives container restart |
| 5.5 LLM mesh timeout | Backend | Budget increased to 45s, proper future cancellation |
| 5.6 Frontend optimization | Frontend | Lazy loading, code splitting, <500KB initial bundle |
| 5.7 Load testing | QA | 100 concurrent users, 95th percentile <2s for login+query |

### Milestone 6: Monitoring (Week 3-4)
**Goal:** Know when things break before users complain.

| Task | Owner | Acceptance Criteria |
|------|-------|---------------------|
| 6.1 Application logs | DevOps | Structured JSON logs, centralized (ELK or Loki) |
| 6.2 Metrics | DevOps | Prometheus exporters for API, DB, Qdrant, Redis |
| 6.3 Dashboards | DevOps | Grafana dashboards for latency, errors, throughput |
| 6.4 Alerts | DevOps | PagerDuty/Slack alerts for: 5xx errors >1%, latency >5s, disk >80% |
| 6.5 Health checks | Backend | `/health` deep check: DB, Qdrant, LLM mesh, all green |
| 6.6 Uptime | DevOps | 99.9% SLA target |

### Milestone 7: CI/CD (Week 4)
**Goal:** Deploy by pushing to `main`.

| Task | Owner | Acceptance Criteria |
|------|-------|---------------------|
| 7.1 GitHub Actions | DevOps | Build + test on every PR |
| 7.2 Staging environment | DevOps | `staging.nrg.iitgn.ac.in` auto-deploys from `develop` |
| 7.3 Production deploy | DevOps | `main` branch auto-deploys to production with approval gate |
| 7.4 Rollback | DevOps | One-click rollback to previous version within 5 minutes |
| 7.5 Database migrations | DevOps | Migrations run automatically, rollback script tested |

### Milestone 8: Documentation (Week 4)
**Goal:** Next engineer can onboard in 1 day.

| Task | Owner | Acceptance Criteria |
|------|-------|---------------------|
| 8.1 Runbook | DevOps | Incident response: database down, mesh failing, Qdrant corrupt |
| 8.2 API documentation | Backend | OpenAPI spec auto-generated, published at `/api/docs` |
| 8.3 Deployment guide | DevOps | Step-by-step: provision → deploy → verify |
| 8.4 Operator manual | DevOps | How to: add user, rotate keys, restore backup, scale up |
| 8.5 Architecture diagrams | Architect | C4 diagrams: context, container, component, code |

---

## 🏗️ PRODUCTION ARCHITECTURE

```
┌─────────────────────────────────────────┐
│           USER (Browser)                │
└─────────────┬───────────────────────────┘
              │ HTTPS
┌─────────────▼───────────────────────────┐
│         Nginx (Reverse Proxy)           │
│  - TLS termination                      │
│  - Rate limiting                        │
│  - Static file serving                  │
└──────┬──────────────┬───────────────────┘
       │              │
┌──────▼──────┐  ┌────▼──────────────────┐
│  Frontend   │  │      Backend API      │
│  (React)    │  │  (FastAPI + Gunicorn) │
│  Container  │  │      4 workers        │
└─────────────┘  └────┬──────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
   ┌────▼────┐  ┌────▼────┐  ┌─────▼─────┐
   │PostgreSQL│  │ Qdrant  │  │   Redis   │
   │  (DB)   │  │(Vectors)│  │  (Cache)  │
   └─────────┘  └─────────┘  └───────────┘
        │             │             │
        └─────────────┴─────────────┘
                      │
              ┌───────▼────────┐
              │  Local LLM     │
              │  (llama.cpp)   │
              │  Port 8080     │
              └────────────────┘
```

---

## 🔐 SECURITY CHECKLIST (Pre-Launch)

- [ ] No hardcoded passwords or API keys in code
- [ ] `.env` files not in git, permissions 600
- [ ] HTTPS only (HSTS header)
- [ ] Security headers: CSP, X-Frame-Options, X-Content-Type-Options
- [ ] SQL injection tested (sqlmap or manual)
- [ ] XSS tested (stored and reflected)
- [ ] CSRF protection on state-changing endpoints
- [ ] Rate limiting enforced
- [ ] Internal services not exposed to internet
- [ ] Container runs as non-root
- [ ] Read-only filesystem where possible
- [ ] Secrets in Vault or encrypted env, not plain text
- [ ] Dependency audit clean
- [ ] Penetration test completed (internal or third-party)

---

## 📊 PERFORMANCE TARGETS

| Metric | Target | Measurement |
|--------|--------|-------------|
| Login latency | <500ms | 95th percentile |
| Query latency (SQL) | <2s | 95th percentile |
| Query latency (LLM mesh) | <15s | 95th percentile |
| Concurrent users | 100 | Load test |
| Uptime | 99.9% | Monthly |
| Error rate | <0.1% | 5xx responses |
| Page load | <3s | Lighthouse |
| Bundle size | <500KB | Gzipped initial |

---

## 🚀 DEPLOYMENT COMMAND (Target State)

```bash
# One command to deploy
git clone https://github.com/iitgn/nrg.git
cd nrg
cp .env.production .env
vim .env  # Set secrets
docker-compose -f docker-compose.prod.yml up -d

# Verify
./scripts/health_check.sh
# Expected: All green
```

---

## 📞 ESCALATION

| Issue | Contact | Response Time |
|-------|---------|---------------|
| Site down | On-call engineer | 15 minutes |
| Security incident | Security lead + IIT GN IT | 1 hour |
| Data corruption | Database admin | 2 hours |
| Auth failure | Backend lead | 4 hours |
| Performance degradation | DevOps | 4 hours |

---

## ✅ GO/NO-GO CRITERIA (Before Launch)

**GO if ALL of these are true:**
1. Milestones 1-5 complete (infra, DB, auth, security, performance)
2. Security checklist 100% complete
3. Load test passed (100 concurrent, <2s p95)
4. Penetration test: no critical or high findings
5. Backup and restore tested successfully
6. Runbook covers 5 common failure scenarios
7. On-call rotation established
8. Domain + SSL working

**NO-GO if ANY of these are true:**
- Demo credentials still in codebase
- SQLite still primary database
- No HTTPS
- No backups
- No monitoring
- No rollback plan

---

## 🛑 STOP WORDS

Do not use these words in production contexts:
- "Demo"
- "Prototype"
- "Temporary"
- "Works on my machine"
- "We'll fix it later"

This is production. It must work. It must be secure. It must be maintained.
