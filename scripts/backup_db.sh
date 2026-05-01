#!/usr/bin/env bash
set -euo pipefail

# Compatibility wrapper kept for older runbooks and cron entries.
# Canonical backup logic lives in scripts/backup_nrg.sh.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec "${ROOT_DIR}/scripts/backup_nrg.sh" "$@"
