#!/usr/bin/env bash
set -euo pipefail

# Local compose helper. Cloud/staging release orchestration lives in
# scripts/deploy.py and scripts/deployment_gate.py.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required for local compose deployment." >&2
  exit 1
fi

if docker compose version >/dev/null 2>&1; then
  COMPOSE=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE=(docker-compose)
else
  echo "Docker Compose is required." >&2
  exit 1
fi

echo "Starting NRG local stack with docker-compose.yml"
"${COMPOSE[@]}" -f docker-compose.yml build
"${COMPOSE[@]}" -f docker-compose.yml up -d

echo "Waiting for API health..."
for _ in $(seq 1 30); do
  if curl -fsS http://localhost:8000/health >/dev/null 2>&1; then
    echo "API health endpoint is reachable."
    exit 0
  fi
  sleep 2
done

echo "API health endpoint did not become reachable within 60 seconds." >&2
exit 1
