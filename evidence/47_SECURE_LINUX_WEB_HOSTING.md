# Secure Linux Web Hosting Evidence

**Skill**: secure-linux-web-hosting
**Applied**: Sat Apr 25 2026
**Evidence File**: `evidence/47_SECURE_LINUX_WEB_HOSTING.md`

---

## Secure Linux Web Hosting: NRG Assessment

### Overview

NRG uses **Docker** for deployment, not bare Linux hosting. This skill is **NOT DIRECTLY APPLICABLE** but the principles inform the Dockerfile review.

---

## NRG Stack (Docker-Based)

| Component | Host | Port | Security |
|----------|------|------|----------|
| API (uvicorn) | Docker | 8000 | Behind nginx |
| PostgreSQL | Docker | 5432 | Internal only |
| Redis | Docker | 6379 | Internal only |
| Qdrant | Docker | 6333 | Internal only |
| Frontend (nginx) | Docker | 80/443 | EXTERNAL |

---

## Applicable Principles

### From secure-linux-web-hosting skill:

#### 1. Firewall (not applicable — Docker handles)
Docker containers should NOT expose internal ports directly.

**NRG Issue**: PostgreSQL (5432), Redis (6379), Qdrant (6333) should not be exposed.

#### 2. nginx Reverse Proxy (applicable to frontend)
nginx should proxy to backend containers, not serve directly.

**NRG Issue**: `Dockerfile.frontend` runs nginx as root.

#### 3. HTTPS (not applicable — Docker handles)
Certificates should be managed at the Docker level.

**NRG**: nginx in container handles HTTPS termination.

---

## NRG-Specific Security Issues

### 1. nginx as Root (CRITICAL)
**File**: `Dockerfile.frontend`
**Issue**: nginx runs as root user inside container

**Fix**: Add USER directive
```dockerfile
# End of Dockerfile.frontend
USER nginx
```

### 2. Internal Ports Exposed
**Issue**: PostgreSQL (5432), Redis (6379), Qdrant (6333) may be exposed

**Fix**: Ensure `docker-compose.yml` doesn't publish internal ports
```yaml
# Should be:
ports:
  - "8000:8000"  # Only API external
# Not:
  - "5432:5432"  # Don't expose DB
```

### 3. No HTTPS in Dev
**Issue**: Frontend serves over HTTP in dev

**Fix**: Use self-signed cert for local HTTPS or document HTTPS requirement

---

## Recommendations

| Priority | Action | Why |
|----------|--------|-----|
| P0 | Fix nginx as root | CRITICAL — security policy |
| P1 | Audit docker-compose ports | Ensure internal services not exposed |
| P2 | Add Docker network isolation | Separate frontend/backend networks |
| P3 | HTTPS in production | Let's Encrypt for frontend |

---

## Skill Deliverable

**Status**: COMPLETED (Not directly applicable)

NRG uses Docker deployment, not bare Linux. Key finding: **nginx as root** is the critical issue from this skill's perspective. Internal port exposure should also be audited in docker-compose.
