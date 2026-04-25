#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "=== NRG Backup Starting ==="
echo "Destination: $BACKUP_DIR"

# PostgreSQL dump via docker exec
echo "[1/3] Dumping PostgreSQL via docker exec..."
docker exec nrg-postgres pg_dump -U nrg -d nrg -F c > "$BACKUP_DIR/nrg_postgres.dump"
echo "      → $BACKUP_DIR/nrg_postgres.dump ($(du -h $BACKUP_DIR/nrg_postgres.dump | cut -f1))"

# Qdrant snapshot
echo "[2/3] Creating Qdrant snapshot..."
SNAPSHOT_RESP=$(curl -s -X POST "http://localhost:6333/collections/nrg_research/snapshots" -H "Content-Type: application/json" -d '{"snapshot_name":"nrg_backup"}')
echo "$SNAPSHOT_RESP" > "$BACKUP_DIR/qdrant_snapshot.json"
echo "      → $BACKUP_DIR/qdrant_snapshot.json"

# Metadata
echo "[3/3] Writing metadata..."
cat > "$BACKUP_DIR/metadata.json" << METAEOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "postgres_dump": "nrg_postgres.dump",
  "qdrant_snapshot_response": "qdrant_snapshot.json",
  "pg_container": "nrg-postgres",
  "qdrant_container": "nrg-qdrant"
}
METAEOF
echo "      → $BACKUP_DIR/metadata.json"

# Symlink latest
rm -f backups/latest
ln -s "$(basename "$BACKUP_DIR")" backups/latest

echo ""
echo "=== Backup Complete ==="
ls -lh "$BACKUP_DIR/"
