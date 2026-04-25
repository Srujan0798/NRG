#!/bin/bash
# Backup NRG database before demo
set -euo pipefail

BACKUP_DIR="/Users/srujansai/Desktop/NRG/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_PATH="/Users/srujansai/Desktop/NRG/nrg_research.db"

mkdir -p "$BACKUP_DIR"

cp "$DB_PATH" "$BACKUP_DIR/nrg_research_$TIMESTAMP.db"
cp "$DB_PATH" "$BACKUP_DIR/nrg_research_latest.db"

echo "Backup complete: $BACKUP_DIR/nrg_research_$TIMESTAMP.db"
ls -lh "$BACKUP_DIR/"