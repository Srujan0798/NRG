#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TS="$(date +"%Y%m%d_%H%M%S")"
LOG_DIR="$ROOT/.protocol/hermetic/$TS"
mkdir -p "$LOG_DIR"
MODE="${MODE:-quick}"                    # quick | full
AGENT_TIMEOUT="${AGENT_TIMEOUT:-5400}"   # per-agent timeout seconds
MIN_QDRANT_POINTS="${MIN_QDRANT_POINTS:-1000}"
# Required: provide your real agent-run commands
required_env=(AGENT1_CMD AGENT2_CMD AGENT3_CMD AGENT4_CMD)
for v in "${required_env[@]}"; do
  if [[ -z "${!v:-}" ]]; then
    echo "[FATAL] Missing env var: $v"
    exit 1
  fi
done
for c in python3 curl; do
  command -v "$c" >/dev/null || { echo "[FATAL] Missing command: $c"; exit 1; }
done
declare -A PIDS
run_agent() {
  local name="$1"
  local cmd="$2"
  local log="$LOG_DIR/${name}.log" 
  echo "[RUN] $name"
  (
    cd "$ROOT"
    bash -lc "$cmd"
  ) >"$log" 2>&1 &
  PIDS["$name"]=$!
}
wait_agent() {
  local name="$1"
  local pid="${PIDS[$name]}"
  local start now elapsed
  start="$(date +%s)"
  while kill -0 "$pid" 2>/dev/null; do
    sleep 2
    now="$(date +%s)"
    elapsed=$((now - start))
    if (( elapsed > AGENT_TIMEOUT )); then
      echo "[TIMEOUT] $name exceeded ${AGENT_TIMEOUT}s"
      kill -TERM "$pid" 2>/dev/null || true
      sleep 2
      kill -KILL "$pid" 2>/dev/null || true
      return 1
    fi
  done
  if wait "$pid"; then
    echo "[OK] $name finished"
    return 0
  else
    echo "[FAIL] $name failed (see $LOG_DIR/${name}.log)"
    return 1
  fi
}
retry_http_200() {
  local url="$1"
  local tries="${2:-20}"
  local delay="${3:-3}"
  local i code
  for ((i=1;i<=tries;i++)); do
    code="$(curl -s -o /dev/null -w "%{http_code}" "$url" || true)"
    if [[ "$code" == "200" ]]; then
      return 0
    fi
    sleep "$delay"
  done
  return 1
}
gate_kong_up() {
  echo "[GATE] Kong up check (:8000)"
  retry_http_200 "http://localhost:8000/health" 25 3
}
gate_api_up() {
  echo "[GATE] API up check (:8001)"
  retry_http_200 "http://localhost:8001/health" 15 2
}
gate_kong_auth_query_dlp() {
  echo "[GATE] Kong auth/query/DLP smoke"
  local login_file token researchers_file query_file dlp_file code
  login_file="$(mktemp)"
  researchers_file="$(mktemp)"
  query_file="$(mktemp)"
  dlp_file="$(mktemp)"
  code="$(curl -sS -o "$login_file" -w "%{http_code}" \
    -X POST "http://localhost:8000/login" \
    -H "Content-Type: application/json" \
    -d '{"username":"researcher_user","password":"researcher-pass"}' || true)"
  [[ "$code" == "200" ]] || { echo "[FAIL] login status=$code"; cat "$login_file"; return 1; }
  token="$(
    python3 - <<'PY' "$login_file"
import json,sys
with open(sys.argv[1]) as f:
    print(json.load(f).get("access_token",""))
PY
  )"
  [[ ${#token} -gt 100 ]] || { echo "[FAIL] invalid token length"; return 1; }
  code="$(curl -sS -o "$researchers_file" -w "%{http_code}" \
    "http://localhost:8000/researchers" \
    -H "Authorization: Bearer $token" || true)"
  [[ "$code" == "200" ]] || { echo "[FAIL] /researchers status=$code"; cat "$researchers_file"; return 1; }
  code="$(curl -sS -o "$query_file" -w "%{http_code}" \
    -X POST "http://localhost:8000/query" \
    -H "Authorization: Bearer $token" \
    -H "Content-Type: application/json" \
    -d '{"query":"Find robotics researchers in Gujarat"}' || true)"
  [[ "$code" == "200" ]] || { echo "[FAIL] /query status=$code"; cat "$query_file"; return 1; }
  # DLP must block PII at gateway
  code="$(curl -sS -o "$dlp_file" -w "%{http_code}" \
    -X POST "http://localhost:8000/query" \
    -H "Authorization: Bearer $token" \
    -H "Content-Type: application/json" \
    -d '{"query":"My Aadhaar is 123456789012"}' || true)"
  [[ "$code" == "400" || "$code" == "403" ]] || { echo "[FAIL] DLP not blocking (status=$code)"; cat "$dlp_file"; return 1; }
  grep -q "DLP_VIOLATION" "$dlp_file" || { echo "[FAIL] DLP response missing DLP_VIOLATION"; cat "$dlp_file"; return 1; }
  echo "[OK] Kong auth/query/DLP smoke passed"
}
gate_sqlite_counts() {
  echo "[GATE] SQLite domain counts"
  python3 - <<'PY' "$ROOT/nrg_research.db"
import sqlite3,sys
db=sys.argv[1]
conn=sqlite3.connect(db)
cur=conn.cursor()
targets=["researchers","institutions","publications","labs","funding_records"]
counts={}
for t in targets:
    cur.execute(f"SELECT COUNT(*) FROM {t}")
    counts[t]=cur.fetchone()[0]
conn.close()
print(counts)
assert counts["researchers"] > 0
assert counts["institutions"] > 0
assert counts["publications"] > 0
assert counts["labs"] > 0
assert counts["funding_records"] > 0
PY
}
gate_qdrant_points() {
  echo "[GATE] Qdrant points >= ${MIN_QDRANT_POINTS}"
  python3 - <<'PY' "$MIN_QDRANT_POINTS"
import requests,sys
min_points=int(sys.argv[1])
base="http://localhost:6333"
cols=requests.get(base+"/collections",timeout=5).json()["result"]["collections"]
names=[c["name"] for c in cols]
assert names, "No Qdrant collections found"
# prefer nrg_research if present
name="nrg_research" if "nrg_research" in names else names[0]
info=requests.get(f"{base}/collections/{name}",timeout=5).json()
points=info["result"].get("points_count",0)
print({"collection":name,"points":points})
assert points >= min_points, f"Insufficient points: {points} < {min_points}"
PY
}
gate_frontend_up() {
  echo "[GATE] Frontend up check (:3000)"
  retry_http_200 "http://localhost:3000" 20 3
}
run_full_tests() {
  echo "[FULL] Running security+UAT checks"
  (cd "$ROOT" && pytest tests/security/test_kong_dlp_runtime.py -q) | tee "$LOG_DIR/full_security.log"
  (cd "$ROOT" && python3 tests/uat/run_all_personas.py) | tee "$LOG_DIR/full_uat.log"
}
echo "=== HERMETIC ORCHESTRATOR START ==="
echo "logs: $LOG_DIR"
# Wave 1: run in parallel
run_agent "agent1_perimeter" "$AGENT1_CMD"
run_agent "agent2_orchestration" "$AGENT2_CMD"
run_agent "agent3_data" "$AGENT3_CMD"
wave1_fail=0
for name in agent1_perimeter agent2_orchestration agent3_data; do
  wait_agent "$name" || wave1_fail=1
done
if (( wave1_fail )); then
  echo "[STOP] Wave 1 failed. Fix logs first: $LOG_DIR"
  exit 1
fi
# Gates after Wave 1
gate_api_up || { echo "[STOP] API gate failed"; exit 1; }
gate_kong_up || { echo "[STOP] Kong gate failed"; exit 1; }
gate_kong_auth_query_dlp || { echo "[STOP] Kong flow gate failed"; exit 1; }
gate_sqlite_counts || { echo "[STOP] SQLite data gate failed"; exit 1; }
gate_qdrant_points || { echo "[STOP] Qdrant gate failed"; exit 1; }
# Wave 2
run_agent "agent4_frontend" "$AGENT4_CMD"
wait_agent "agent4_frontend" || { echo "[STOP] Wave 2 failed"; exit 1; }
gate_frontend_up || { echo "[STOP] Frontend gate failed"; exit 1; }
if [[ "$MODE" == "full" ]]; then
  run_full_tests
fi
echo "=== HERMETIC ORCHESTRATOR SUCCESS ==="
echo "All gates passed. Evidence logs in: $LOG_DIR"