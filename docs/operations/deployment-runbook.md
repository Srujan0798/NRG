# NRG Deployment Runbook

## Overview

This document lists all environment variables required to run the National Research Graph (NRG) platform in production.

---

## Critical — Must Be Set

These variables have **no defaults** and will cause the application to fail at startup if missing.

| Variable | Purpose | Example |
|----------|---------|---------|
| `RESEARCHER_PASSWORD` | Password for the seeded `researcher_user` account | `researcher-pass` |
| `GOV_PASSWORD` | Password for the seeded `gov_user` account | `government-pass` |
| `INDUSTRY_PASSWORD` | Password for the seeded `industry_user` account | `industry-pass` |

> **Security Note:** These passwords are loaded via `_require_env()` in `src/auth/jwt_handler.py`. There are no fallbacks. The application will raise `RuntimeError` and refuse to start if any are unset.

---

## Required — Production Override Recommended

These variables have defaults suitable for local development but **must be overridden in production**.

### Database

| Variable | Default | Purpose |
|----------|---------|---------|
| `DATABASE_URL` | `sqlite:///...` (local file) | PostgreSQL connection string. Must be PostgreSQL in production. |

**Production Example:**
```bash
DATABASE_URL=postgresql://nrg:STRONG_PASSWORD@postgres:5432/nrg
```

### JWT / Authentication

| Variable | Default | Purpose |
|----------|---------|---------|
| `JWT_SECRET` | *(none)* | Symmetric secret for legacy token paths. Prefer RS256 keys. |
| `JWT_PRIVATE_KEY_PATH` | `infrastructure/kong/ssl/jwt_rsa.key` | Path to RSA private key for RS256 signing |
| `JWT_PUBLIC_KEY_PATH` | `infrastructure/kong/ssl/jwt_rsa.pub` | Path to RSA public key for RS256 verification |
| `JWT_ALGORITHM` | `RS256` | Token signing algorithm (`RS256` or `HS256`) |

> **Security Note:** Generate unique RSA keypairs per environment. Never commit keys to version control.

### Vector Database (Qdrant)

| Variable | Default | Purpose |
|----------|---------|---------|
| `QDRANT_HOST` | `localhost` | Qdrant server hostname |
| `QDRANT_PORT` | `6333` | Qdrant server port |
| `QDRANT_COLLECTION` | `nrg_research` | Qdrant collection name |

### LLM Provider

| Variable | Default | Purpose |
|----------|---------|---------|
| `LLM_PROVIDER` | *(none)* | Primary LLM provider: `minimax`, `nvidia`, `google`, `openai` |
| `LLM_FALLBACK_ORDER` | *(none)* | Comma-separated fallback providers |

Provider-specific API keys (at least one must be set):

| Variable | Required For |
|----------|--------------|
| `MINIMAX_API_KEY` | Minimax provider |
| `MINIMAX_MODEL` | Minimax model selection (default: `minimax-m2.7`) |
| `NVIDIA_API_KEY` | NVIDIA NIM provider |
| `NVIDIA_MODEL` | NVIDIA model selection (default: `meta/llama-3.1-70b-instruct`) |
| `GOOGLE_API_KEY` | Google Gemini provider |
| `OPENAI_API_KEY` | OpenAI provider |

---

## Docker Compose / Infrastructure

These are used by `docker-compose.yml` and should be set in production.

| Variable | Default | Purpose |
|----------|---------|---------|
| `POSTGRES_USER` | `nrg` | PostgreSQL superuser name |
| `POSTGRES_PASSWORD` | `nrg_default_password` | **Must be changed in production** |
| `POSTGRES_DB` | `nrg` | PostgreSQL database name |
| `POSTGRES_PORT` | `5432` | Host-bound PostgreSQL port |
| `APP_ENV` | `dev` | Environment identifier: `dev`, `staging`, `prod` |

---

## Optional — Tuning & Features

### API Behavior

| Variable | Default | Purpose |
|----------|---------|---------|
| `LOG_LEVEL` | `INFO` | Logging verbosity: `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated allowed frontend origins |
| `NRG_QUOTA_DISABLED` | *(unset)* | Set to `1` or `true` to disable rate limiting |
| `NRG_DEEP_HEALTH_CHECKS` | *(unset)* | Set to `1` or `true` to enable Qdrant/DB deep health checks |
| `NRG_DATA_RETENTION_DAYS` | `90` | DPDP Act 2023 data retention period |
| `NRG_SOVEREIGNTY_ENFORCED` | `1` | Set to `0` to disable data-sovereignty egress guards |

### LLM Tuning

| Variable | Default | Purpose |
|----------|---------|---------|
| `LLM_TIMEOUT_BUDGET` | `45` | Total seconds allowed for LLM mesh response |
| `LLM_REQUEST_TIMEOUT_SECONDS` | `60` | Per-provider HTTP timeout |
| `CLOUD_SYNTHESIS_ALLOWED` | `true` | Enable cloud LLM fallback |

### Embedding Models

| Variable | Default | Purpose |
|----------|---------|---------|
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Primary embedding model |
| `EMBEDDING_FALLBACK_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Fallback embedding model |

### Local LLM (Optional)

| Variable | Default | Purpose |
|----------|---------|---------|
| `LOCAL_LLM_DISABLED` | `false` | Set to `true` to disable local LLM entirely |
| `LOCAL_LLM_MODEL` | `microsoft/phi-2` | HuggingFace model for local inference |
| `LOCAL_LLM_MAX_LENGTH` | `512` | Max token length for local generation |
| `LOCAL_LLM_ENABLE_HF` | `false` | Enable HuggingFace transformers fallback |
| `LLAMA_CPP_URL` | `http://localhost:8080` | llama.cpp server URL |
| `LLAMA_CPP_TIMEOUT` | `120` | llama.cpp request timeout |

### PII / Security

| Variable | Default | Purpose |
|----------|---------|---------|
| `PII_ENCRYPTION_KEY` | *(none)* | AES key for PII tokenization |
| `PII_ENCRYPTION_SALT` | *(none)* | Salt for PII tokenization |

> **Security Note:** `PII_ENCRYPTION_KEY` must be 32 bytes (64 hex chars). Generate with: `openssl rand -hex 32`

### Frontend Build-Time

| Variable | Default | Purpose |
|----------|---------|---------|
| `VITE_API_URL` | `http://localhost:8000` | Backend API URL (used at build time) |

---

## Quick Start Checklist

Before deploying to production, verify:

- [ ] `RESEARCHER_PASSWORD`, `GOV_PASSWORD`, `INDUSTRY_PASSWORD` are strong and unique
- [ ] `DATABASE_URL` points to a managed PostgreSQL instance (not SQLite)
- [ ] `POSTGRES_PASSWORD` is strong and different from the default
- [ ] JWT RSA keypair is generated and paths are correct
- [ ] At least one LLM provider API key is set and has quota
- [ ] `CORS_ORIGINS` includes your production frontend domain
- [ ] `PII_ENCRYPTION_KEY` and `PII_ENCRYPTION_SALT` are set for PII handling
- [ ] `APP_ENV=prod` is set in docker-compose or container environment
- [ ] `NRG_SOVEREIGNTY_ENFORCED=1` is confirmed for production
- [ ] HuggingFace models are pre-downloaded (or `HF_TOKEN` is set for higher rate limits)

---

## Example `.env.prod` File

```bash
# === App Environment ===
APP_ENV=prod
LOG_LEVEL=INFO

# === Auth (REQUIRED — no defaults) ===
RESEARCHER_PASSWORD=change-me-strong-password-1
GOV_PASSWORD=change-me-strong-password-2
INDUSTRY_PASSWORD=change-me-strong-password-3

# === JWT ===
JWT_ALGORITHM=RS256
JWT_PRIVATE_KEY_PATH=/secrets/jwt_rsa.key
JWT_PUBLIC_KEY_PATH=/secrets/jwt_rsa.pub

# === Database ===
DATABASE_URL=postgresql://nrg:STRONG_DB_PASSWORD@postgres:5432/nrg
POSTGRES_USER=nrg
POSTGRES_PASSWORD=STRONG_DB_PASSWORD
POSTGRES_DB=nrg

# === Qdrant ===
QDRANT_HOST=qdrant
QDRANT_PORT=6333
QDRANT_COLLECTION=nrg_research

# === LLM Provider (pick at least one) ===
LLM_PROVIDER=minimax
LLM_FALLBACK_ORDER=minimax,nvidia
MINIMAX_API_KEY=sk-...
MINIMAX_MODEL=minimax-m2.7
NVIDIA_API_KEY=nvapi-...
NVIDIA_MODEL=meta/llama-3.1-70b-instruct

# === CORS ===
CORS_ORIGINS=https://nrg.gov.in,https://admin.nrg.gov.in

# === Security ===
NRG_SOVEREIGNTY_ENFORCED=1
NRG_DATA_RETENTION_DAYS=90
PII_ENCRYPTION_KEY=GENERATE_WITH_OPENSSL_RAND_HEX_32
PII_ENCRYPTION_SALT=GENERATE_WITH_OPENSSL_RAND_HEX_16

# === Optional Tuning ===
LLM_TIMEOUT_BUDGET=45
LLM_REQUEST_TIMEOUT_SECONDS=60
UVICORN_WORKERS=4
```

---

## Troubleshooting

### "Production requires RESEARCHER_PASSWORD to be set in environment"
One of the three seeded user passwords is missing. Set all three: `RESEARCHER_PASSWORD`, `GOV_PASSWORD`, `INDUSTRY_PASSWORD`.

### API takes 60+ seconds to start
Normal on first boot — sentence-transformers downloads embedding models from HuggingFace. Subsequent starts use the local cache (~5-10s). Set `HF_TOKEN` for higher HuggingFace rate limits.

### Health check returns empty response during startup
The API is still loading models. Wait for the "Application startup complete" log line. Consider increasing health check `start_period` in docker-compose.

### "Endpoint rate limit exceeded" on `/query`
Expected behavior. Gov/Industry tiers are limited to 10 requests/minute. Researcher tier is 60/minute. Stagger concurrent requests or temporarily set `NRG_QUOTA_DISABLED=1` for load testing.
