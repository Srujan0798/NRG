# POINTER: Tech Stack

> **Do not trust this file as the source of truth.** Read the actual files listed below to verify what tech is used, what version, where.

## Where to Read

| Layer | Actual Source Files | What to Verify |
|-------|--------------------|----------------|
| **Backend deps** | `pyproject.toml`, `requirements.txt` | Python packages, versions |
| **Frontend deps** | `frontend/package.json` | Node packages, versions |
| **Database** | `docker-compose.yml` (postgres image), `db_struct.sql` | PostgreSQL 16 |
| **Vector Store** | `docker-compose.yml` (qdrant image) | Qdrant version |
| **Cache** | `docker-compose.yml` (redis image) | Redis version |
| **Build tool** | `frontend/vite.config.ts` | Vite version |
| **Test runner** | `pytest.ini`, `frontend/package.json` | Pytest, Jest versions |
| **CI/CD** | `.github/workflows/` | GitHub Actions configs |

## Verification Commands

```bash
# Backend packages
grep -E "^dependencies|^\[" pyproject.toml | head -20
cat requirements.txt 2>/dev/null || echo "No requirements.txt"

# Frontend packages
grep -E '"react"|"vite"|"tailwind"|"jest"|"playwright"' frontend/package.json

# Docker images
grep "image:" docker-compose.yml

# Vite config
ls frontend/vite.config.ts

# CI workflows
ls .github/workflows/
```

**Read the actual source files. Do not trust this pointer.**
