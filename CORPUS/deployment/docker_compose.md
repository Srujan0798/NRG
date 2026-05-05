# POINTER: Docker Compose

> **Do not trust this file as the source of truth.** Read the actual files listed below.

## Where to Read

| Topic | Actual Source Files | What to Verify |
|-------|--------------------|----------------|
| **Services** | `docker-compose.yml`, `docker-compose.prod.yml`, `docker-compose.dev.yml` | All services defined, ports, env vars |
| **API Dockerfile** | `Dockerfile.api` | Build steps, base image |
| **Frontend Dockerfile** | `Dockerfile.frontend` | Build steps, nginx base |
| **Env Config** | `.env`, `.env.dev`, `.env.prod` | Database URL, secrets, feature flags |

## Verification Commands

```bash
# Validate docker compose
docker compose config > /dev/null && echo "VALID" || echo "INVALID"

# Check services
docker compose config --services

# Check Dockerfiles
ls Dockerfile.api Dockerfile.frontend Dockerfile.nginx

# Check env files
ls .env .env.dev .env.prod .env.staging
```

**Read the actual source files. Do not trust this pointer.**
