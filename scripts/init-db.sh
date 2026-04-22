#!/bin/bash
# ==============================================================================
# init-db.sh - Initialize database and run migrations
# ==============================================================================

set -e

echo "[init-db] Starting database initialization..."

DATABASE_URL="${DATABASE_URL:-postgresql://nrg:nrg_secret@postgres:5432/nrg}"

echo "[init-db] Running Alembic migrations..."
cd /app
python -m alembic upgrade head

echo "[init-db] Database initialization complete."