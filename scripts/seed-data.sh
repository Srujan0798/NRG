#!/bin/bash
# ==============================================================================
# seed-data.sh - Seed initial data for development/staging
# ==============================================================================

set -e

echo "[seed-data] Seeding initial data..."

cd /app

# Check if data already exists
RESEARCHER_COUNT=$(python -c "
from src.data.database_v2 import NRGDatabase
db = NRGDatabase('${DATABASE_URL}')
with db.get_session() as s:
    from sqlalchemy import func, text
    result = s.execute(text('SELECT COUNT(*) FROM researchers'))
    print(result.scalar())
" 2>/dev/null || echo "0")

if [ "$RESEARCHER_COUNT" -gt 0 ]; then
    echo "[seed-data] Database already has $RESEARCHER_COUNT researchers, skipping seed."
    exit 0
fi

echo "[seed-data] Running seed script..."
python scripts/seed_database.py

echo "[seed-data] Seeding complete."