#!/bin/bash
# Backup NRG database
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="${NRG_BACKUP_DIR:-$REPO/backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_PATH="${NRG_DB_PATH:-$REPO/nrg_research.db}"

mkdir -p "$BACKUP_DIR"

cp "$DB_PATH" "$BACKUP_DIR/nrg_research_$TIMESTAMP.db"
cp "$DB_PATH" "$BACKUP_DIR/nrg_research_latest.db"

echo "Backup complete: $BACKUP_DIR/nrg_research_$TIMESTAMP.db"
ls -lh "$BACKUP_DIR/"