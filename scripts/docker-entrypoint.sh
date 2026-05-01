#!/bin/bash
# ==============================================================================
# Docker Entrypoint Script for NRG API
# Handles graceful shutdown, migrations, and service readiness
# ==============================================================================

set -e

echo "[entrypoint] Starting NRG API..."

# Wait for dependent services
echo "[entrypoint] Waiting for PostgreSQL..."
/scripts/wait-for-it.sh "${POSTGRES_HOST:-postgres}:${POSTGRES_PORT:-5432}" --timeout=60 --quiet

echo "[entrypoint] Waiting for Redis..."
/scripts/wait-for-it.sh "${REDIS_HOST:-redis}:${REDIS_PORT:-6379}" --timeout=30 --quiet

echo "[entrypoint] Waiting for Qdrant..."
/scripts/wait-for-it.sh "${QDRANT_HOST:-qdrant}:${QDRANT_PORT:-6333}" --timeout=30 --quiet

# Run database migrations if needed
if [ "${SKIP_MIGRATIONS:-false}" != "true" ]; then
    echo "[entrypoint] Running database migrations..."
    python -m alembic upgrade head || echo "[entrypoint] Migrations skipped (Alembic not configured)"
fi

# Seed initial data in development
if [ "${APP_ENV:-dev}" = "dev" ] && [ "${SEED_DATA:-false}" = "true" ]; then
    echo "[entrypoint] Seeding development data..."
    python scripts/seed_database.py || echo "[entrypoint] Seeding skipped"
fi

echo "[entrypoint] Starting uvicorn server..."

# Graceful shutdown handled by SIGTERM to uvicorn
exec uvicorn src.api.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers "${UVICORN_WORKERS:-4}" \
    --loop "${UVICORN_LOOP:-uvloop}" \
    --http "${UVICORN_HTTP:-httptools}" \
    --timeout-keep-alive "${UVICORN_TIMEOUT_KEEP_ALIVE:-5}" \
    --graceful-timeout "${UVICORN_GRACEFUL_TIMEOUT:-30}"
