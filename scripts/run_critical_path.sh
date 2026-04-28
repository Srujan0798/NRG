#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EVIDENCE_DATE="${NRG_EVIDENCE_DATE:-2026-04-28}"
EVIDENCE_DIR="${ROOT_DIR}/evidence/${EVIDENCE_DATE}/critical_path"
API_BASE="${API_BASE:-http://localhost:8000}"
FRONTEND_BASE="${FRONTEND_BASE:-http://localhost:5173}"
APP_ENV_VALUE="${APP_ENV:-dev}"
STRICT=0
RESET=0
WALK=0
SKIP_DOCKER=0

usage() {
  cat <<'EOF'
Usage: bash scripts/run_critical_path.sh [--strict] [--reset] [--walk] [--skip-docker]

Options:
  --strict       Fail fast on degraded health, low data scale, or prewarm errors.
  --reset        Stop the compose stack and remove volumes before booting.
  --walk         Run the Playwright 10-step acceptance walk after boot.
  --skip-docker  Assume the API/frontend are already running.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --strict) STRICT=1 ;;
    --reset) RESET=1 ;;
    --walk) WALK=1 ;;
    --skip-docker) SKIP_DOCKER=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage; exit 2 ;;
  esac
  shift
done

cd "${ROOT_DIR}"
mkdir -p "${EVIDENCE_DIR}"

log() { printf '\n[%s] %s\n' "$(date +%H:%M:%S)" "$*"; }
ok() { printf 'OK: %s\n' "$*"; }
warn() { printf 'WARN: %s\n' "$*" >&2; }
fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || fail "$1 is required"
}

compose() {
  APP_ENV="${APP_ENV_VALUE}" FRONTEND_PORT=5173 docker compose \
    -f docker-compose.yml \
    -f docker-compose.prod.yml \
    "$@"
}

wait_tcp() {
  local host="$1"
  local port="$2"
  local label="$3"
  local timeout="${4:-90}"
  python3 - "$host" "$port" "$label" "$timeout" <<'PY'
import socket
import sys
import time

host, port, label, timeout = sys.argv[1], int(sys.argv[2]), sys.argv[3], float(sys.argv[4])
deadline = time.time() + timeout
while time.time() < deadline:
    try:
        with socket.create_connection((host, port), timeout=2):
            print(f"OK: {label} reachable on {host}:{port}")
            raise SystemExit(0)
    except OSError:
        time.sleep(1)
print(f"FAIL: {label} not reachable on {host}:{port}", file=sys.stderr)
raise SystemExit(1)
PY
}

wait_http() {
  local url="$1"
  local label="$2"
  local timeout="${3:-120}"
  local deadline=$((SECONDS + timeout))
  until curl -fsS "${url}" >/dev/null 2>&1; do
    if (( SECONDS >= deadline )); then
      fail "${label} did not become ready at ${url}"
    fi
    sleep 2
  done
  ok "${label} ready at ${url}"
}

validate_env() {
  python3 - <<'PY'
from pathlib import Path
import sys

required = {
    "JWT_PRIVATE_KEY_PATH",
    "JWT_PUBLIC_KEY_PATH",
    "JWT_ISSUER",
    "JWT_AUDIENCE",
    "JWT_EXPIRY_SECONDS",
}
env = {}
for line in Path(".env").read_text().splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    key, value = line.split("=", 1)
    env[key] = value
missing = sorted(key for key in required if not env.get(key))
if missing:
    print(f"Missing .env keys: {', '.join(missing)}", file=sys.stderr)
    raise SystemExit(1)
if env.get("JWT_ISSUER") != "nrg-iitgn":
    print("JWT_ISSUER must be nrg-iitgn", file=sys.stderr)
    raise SystemExit(1)
if env.get("JWT_AUDIENCE") != "nrg-clients":
    print("JWT_AUDIENCE must be nrg-clients", file=sys.stderr)
    raise SystemExit(1)
if env.get("JWT_EXPIRY_SECONDS") != "3600":
    print("JWT_EXPIRY_SECONDS must be 3600", file=sys.stderr)
    raise SystemExit(1)
PY
}

validate_health() {
  local health_file="${EVIDENCE_DIR}/health.json"
  local all_file="${EVIDENCE_DIR}/health_all.json"
  curl -fsS "${API_BASE}/health" > "${health_file}"
  curl -fsS "${API_BASE}/health/all" > "${all_file}" || true
  python3 - "${health_file}" "${STRICT}" <<'PY'
import json
import sys

path = sys.argv[1]
strict = sys.argv[2] == "1"
health = json.load(open(path))
status = health.get("status")
database = health.get("database") or {}
audit = health.get("audit") or {}
retriever = health.get("retriever") or {}
auth = health.get("auth_status") or {}
tables = database.get("tables") or database.get("table_count")
chain_valid = audit.get("chain_valid")

required_ok = status == "healthy" and auth.get("status") not in {"unhealthy"}
if strict:
    required_ok = required_ok and chain_valid is True and tables in {58, 73}
else:
    required_ok = required_ok and (tables is None or int(tables) >= 1)

print(json.dumps({
    "status": status,
    "tables": tables,
    "chain_valid": chain_valid,
    "retriever_status": retriever.get("status"),
    "auth_status": auth.get("status"),
}, indent=2, sort_keys=True))

if not required_ok:
    raise SystemExit(1)
PY
}

write_summary() {
  local summary="${EVIDENCE_DIR}/walk_summary.md"
  {
    echo "# Critical Path Walk Summary"
    echo
    echo "- Captured at: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "- Commit: $(git rev-parse HEAD 2>/dev/null || echo unknown)"
    echo "- API: ${API_BASE}"
    echo "- Frontend: ${FRONTEND_BASE}"
    echo "- Strict: ${STRICT}"
    echo "- Walk: ${WALK}"
  } > "${summary}"
}

log "Preflight"
require_cmd python3
require_cmd curl
if [[ "${SKIP_DOCKER}" -eq 0 ]]; then
  require_cmd docker
fi
[[ -f .env ]] || fail ".env is missing"
validate_env
bash scripts/generate_jwt_keys.sh
python3 scripts/seed_acceptance_users.py --json > "${EVIDENCE_DIR}/acceptance_users_local.json"
ok "environment and acceptance personas verified locally"

if [[ "${SKIP_DOCKER}" -eq 0 ]]; then
  if [[ "${RESET}" -eq 1 ]]; then
    log "Reset compose volumes"
    compose down -v --remove-orphans || true
  fi

  log "Boot compose stack"
  compose up -d --build postgres pgbouncer qdrant redis api frontend
  wait_tcp localhost 5432 "Postgres" 90
  wait_tcp localhost 6333 "Qdrant" 90
  wait_tcp localhost 6379 "Redis" 90
  wait_tcp localhost 8000 "API" 120
  wait_tcp localhost 5173 "Frontend" 120
else
  log "Using already-running stack"
fi

wait_http "${API_BASE}/health" "API health" 120
wait_http "${FRONTEND_BASE}" "Frontend" 120

log "Migrate"
if [[ "${SKIP_DOCKER}" -eq 0 ]]; then
  if ! compose exec -T api python -m alembic upgrade head; then
    [[ "${STRICT}" -eq 1 ]] && fail "alembic migration failed"
    warn "alembic migration failed; continuing because --strict was not set"
  fi
elif ! python3 -m alembic upgrade head; then
  [[ "${STRICT}" -eq 1 ]] && fail "alembic migration failed"
  warn "alembic migration failed; continuing because --strict was not set"
fi

log "Verify acceptance users through API"
python3 scripts/seed_acceptance_users.py --verify-api "${API_BASE}" --json > "${EVIDENCE_DIR}/acceptance_users_api.json"
ok "three acceptance personas log in through API"

log "Acceptance data preflight"
if [[ "${STRICT}" -eq 1 ]]; then
  python3 scripts/seed_acceptance_data.py --api-base "${API_BASE}" --strict --json > "${EVIDENCE_DIR}/acceptance_data.json"
else
  python3 scripts/seed_acceptance_data.py --api-base "${API_BASE}" --json > "${EVIDENCE_DIR}/acceptance_data.json" || true
fi

log "Prewarm acceptance cache"
if ! python3 scripts/prewarm_acceptance_cache.py --all > "${EVIDENCE_DIR}/prewarm.log" 2>&1; then
  [[ "${STRICT}" -eq 1 ]] && fail "acceptance cache prewarm failed; see ${EVIDENCE_DIR}/prewarm.log"
  warn "acceptance cache prewarm failed; see ${EVIDENCE_DIR}/prewarm.log"
fi

log "Health validation"
if ! validate_health > "${EVIDENCE_DIR}/health_summary.json"; then
  fail "health validation failed; see ${EVIDENCE_DIR}/health.json"
fi
ok "health validation passed"

if [[ "${WALK}" -eq 1 ]]; then
  log "Playwright acceptance walk"
  (cd frontend && PLAYWRIGHT_BASE_URL="${FRONTEND_BASE}" npx playwright test -c playwright.critical.config.ts)
  ok "acceptance walk passed"
else
  warn "Playwright walk skipped; rerun with --walk to capture PNGs and MP4"
fi

write_summary

printf '\nPASS: READY - %s\n' "${FRONTEND_BASE}"
printf 'T1: researcher@iitgn.ac.in / Researcher@2026\n'
printf 'T2: ministry@nrg.gov.in / Ministry@2026\n'
printf 'T3: partner@industry.in / Industry@2026\n'
