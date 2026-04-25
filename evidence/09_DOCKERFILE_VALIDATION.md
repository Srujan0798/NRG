# Dockerfile Validation Report — Session 92

**Date:** 2026-04-25
**Tool:** Manual hadolint-style checks (hadolint not installed)
**Files:** `Dockerfile.api`, `Dockerfile.frontend`

---

## Dockerfile.api — Overall: PASS

| Check | Result |
|-------|--------|
| Root user | ✅ PASS — `USER app` at line 62 |
| Hardcoded secrets | ✅ PASS — No passwords/secrets in ENV/ARG |
| `:latest` tag | ✅ PASS — Uses `python:3.11-slim` |
| HEALTHCHECK | ✅ PASS — Line 77: curl-based health check |
| EXPOSE | ✅ PASS — Port 8000 |
| pip --no-cache-dir | ✅ PASS — Line 29 |
| Multi-stage | ✅ PASS — Builder + Runner stages |

### Medium Issues

**Issue M1: pip install without version-pinned requirements**
`Dockerfile.api:29` — `pip install --no-cache-dir -e .` installs from `pyproject.toml` without pinning versions. In production, this can lead to non-deterministic builds.

**Fix:** Add a requirements freeze step:
```dockerfile
RUN pip install pip-tools && pip-compile pyproject.toml -o requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
```

---

## Dockerfile.frontend — Overall: PARTIAL PASS

| Check | Result |
|-------|--------|
| Root user | ⚠️  FAIL — nginx runs as root |
| `:latest` tag | ✅ PASS |
| HEALTHCHECK | ✅ PASS — wget-based |
| npm ci | ✅ PASS |
| nginx config | ✅ PASS |

### Critical Issues

**Issue C1: nginx Runs as Root**
`Dockerfile.frontend:29` — `FROM nginx:1.25-alpine` runs nginx as root by default. NGINX should run as a non-root user for security.

**Fix:**
```dockerfile
FROM nginx:1.25-alpine
# Create non-root user for nginx
RUN addgroup -g 101 -S nginx && adduser -S nginx -u 101
RUN sed -i 's/listen\(.*\)80;/listen 8080;/' /etc/nginx/nginx.conf \
    && sed -i 's/user nginx;/user nginx;/' /etc/nginx/nginx.conf
USER nginx
EXPOSE 8080
```

**Issue C2: EXPOSE 80 but nginx on 8080**
If fixing C1, update EXPOSE to match the actual port.

### Medium Issues

**Issue M2: No `.dockerignore` verification**
No `.dockerignore` checked for the frontend directory. Large `node_modules` could be copied into the build context unnecessarily.

**Fix:** Ensure `frontend/.dockerignore` or root `.dockerignore` excludes:
```
node_modules
dist
.git
*.log
```

---

## Recommended Fixes (Priority Order)

1. **[C1]** Fix nginx root user — `Dockerfile.frontend`
2. **[M1]** Add requirements freeze — `Dockerfile.api`
3. **[C2]** Update EXPOSE to match nginx port
4. **[M2]** Verify `.dockerignore` exists and is effective

---

## Fast Path: Both Dockerfiles pass core security checks. No critical secrets or root user issues in API Dockerfile. Frontend nginx needs USER directive.
