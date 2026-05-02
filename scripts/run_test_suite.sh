#!/usr/bin/env bash
# LB-4: Run full pytest suite with parallel execution and JUnit output.
# Target: <5 minutes for the default non-slow suite on an 8-core machine.
# Usage: ./scripts/run_test_suite.sh [--coverage] [--slow] [evidence_dir] [pytest args...]

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WITH_COVERAGE=0
INCLUDE_SLOW=0
RUN_LIVE_API=0
PYTEST_EXTRA_ARGS=()
EVIDENCE_DIR="${EVIDENCE_DIR:-}"
LIVE_API_BASE="${API_BASE:-${NRG_BASE_URL:-${NRG_API_URL:-http://localhost:8000}}}"
LIVE_API_READY_PATH="${LIVE_API_READY_PATH:-/health/db}"
LIVE_API_HEALTH_TIMEOUT="${LIVE_API_HEALTH_TIMEOUT:-10}"
LIVE_API_HOST="${LIVE_API_HOST:-127.0.0.1}"
LIVE_API_PORT="${LIVE_API_PORT:-8000}"
LIVE_API_LOG=""
LIVE_API_PID=""
TEST_AUDIT_BASE=""
LIVE_API_AUDIT_DIR=""
LIVE_TEST_PATHS=(
    "tests/api/test_tier_isolation_live.py"
    "tests/security/test_red_team_v41.py"
)

while [[ $# -gt 0 ]]; do
    case "$1" in
        --coverage)
            WITH_COVERAGE=1
            shift
            ;;
        --slow)
            INCLUDE_SLOW=1
            shift
            ;;
        --live-api)
            RUN_LIVE_API=1
            shift
            ;;
        --)
            shift
            PYTEST_EXTRA_ARGS+=("$@")
            break
            ;;
        -*)
            PYTEST_EXTRA_ARGS+=("$1")
            shift
            ;;
        *)
            if [[ -z "$EVIDENCE_DIR" ]]; then
                EVIDENCE_DIR="$1"
            else
                PYTEST_EXTRA_ARGS+=("$1")
            fi
            shift
            ;;
    esac
done

if [[ -z "$EVIDENCE_DIR" ]]; then
    EVIDENCE_DIR="$REPO_ROOT/evidence/$(date +%Y-%m-%d)"
fi
mkdir -p "$EVIDENCE_DIR"
TEST_AUDIT_BASE="${NRG_TEST_AUDIT_BASE:-$EVIDENCE_DIR/audit_chain}"
LIVE_API_AUDIT_DIR="${LIVE_API_AUDIT_DIR:-${NRG_AUDIT_DIR:-$EVIDENCE_DIR/live_api_audit}}"
mkdir -p "$TEST_AUDIT_BASE" "$LIVE_API_AUDIT_DIR"
export NRG_TEST_ISOLATE_AUDIT=1
export NRG_TEST_AUDIT_BASE="$TEST_AUDIT_BASE"

JUNIT_XML="$EVIDENCE_DIR/test_suite_full_final.xml"
LIVE_JUNIT_XML="$EVIDENCE_DIR/test_suite_live_api.xml"
COVERAGE_XML="$EVIDENCE_DIR/coverage.xml"
if [[ -z "${PYTHON_BIN:-}" && -x "$REPO_ROOT/.venv/bin/python" ]]; then
    PYTHON_BIN="$REPO_ROOT/.venv/bin/python"
else
    PYTHON_BIN="${PYTHON_BIN:-python3}"
fi

api_ready() {
    "$PYTHON_BIN" - "$LIVE_API_BASE" "$LIVE_API_READY_PATH" "$LIVE_API_HEALTH_TIMEOUT" <<'PY'
import json
import sys
import urllib.error
import urllib.request

base = sys.argv[1].rstrip("/")
path = sys.argv[2]
timeout = float(sys.argv[3])
url = f"{base}{path if path.startswith('/') else '/' + path}"
try:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        if not (200 <= response.status < 500):
            raise SystemExit(1)
        if path.rstrip("/") == "/health/db":
            payload = json.loads(response.read().decode("utf-8"))
            raise SystemExit(0 if payload.get("ready") is True else 1)
        raise SystemExit(0)
except (OSError, urllib.error.URLError, json.JSONDecodeError):
    raise SystemExit(1)
PY
}

cleanup_live_api() {
    if [[ -n "$LIVE_API_PID" ]]; then
        kill "$LIVE_API_PID" >/dev/null 2>&1 || true
        wait "$LIVE_API_PID" >/dev/null 2>&1 || true
        kill -9 "$LIVE_API_PID" >/dev/null 2>&1 || true
    fi
}

start_live_api_if_needed() {
    if api_ready; then
        echo "  Live API:      existing service at $LIVE_API_BASE"
        return
    fi

    LIVE_API_LOG="$EVIDENCE_DIR/live_api_server.log"
    echo "  Live API:      starting uvicorn at $LIVE_API_BASE"
    (
        cd "$REPO_ROOT"
        NRG_ENV="${NRG_ENV:-dev}" \
        NRG_QUOTA_DISABLED="${NRG_QUOTA_DISABLED:-1}" \
        NRG_AUDIT_DIR="$LIVE_API_AUDIT_DIR" \
        DATABASE_URL="${DATABASE_URL:-sqlite:///nrg_research.db}" \
        "$PYTHON_BIN" -m uvicorn src.api.main:app \
            --host "$LIVE_API_HOST" \
            --port "$LIVE_API_PORT"
    ) >"$LIVE_API_LOG" 2>&1 &
    LIVE_API_PID="$!"
    trap cleanup_live_api EXIT

    for _ in $(seq 1 90); do
        if api_ready; then
            echo "  Live API log:  $LIVE_API_LOG"
            return
        fi
        if ! kill -0 "$LIVE_API_PID" >/dev/null 2>&1; then
            echo "ERROR: live API exited before readiness. Log: $LIVE_API_LOG" >&2
            tail -80 "$LIVE_API_LOG" >&2 || true
            return 1
        fi
        sleep 1
    done

    echo "ERROR: live API did not become ready. Log: $LIVE_API_LOG" >&2
    tail -80 "$LIVE_API_LOG" >&2 || true
    return 1
}

echo "═══════════════════════════════════════════════════════"
echo "  NRG Full Test Suite"
echo "  Evidence dir: $EVIDENCE_DIR"
echo "  JUnit XML:    $JUNIT_XML"
echo "  Test audit:   $TEST_AUDIT_BASE/{worker}"
if [[ "$RUN_LIVE_API" -eq 1 ]]; then
    echo "  Live JUnit:   $LIVE_JUNIT_XML"
    echo "  Live audit:   $LIVE_API_AUDIT_DIR"
fi
echo "═══════════════════════════════════════════════════════"

TIMEFORMAT='Suite completed in %R seconds'
START_SECONDS=$SECONDS
time {
    cd "$REPO_ROOT"
    PYTEST_ARGS=(
        tests/
        -n auto
        --dist=loadgroup
        --junitxml="$JUNIT_XML"
        --ignore=tests/api/test_tier_isolation_live.py
        --ignore=tests/security/test_red_team_v41.py
    )

    if [[ "$WITH_COVERAGE" -eq 1 ]]; then
        export COVERAGE_FILE="$EVIDENCE_DIR/.coverage"
        PYTEST_ARGS+=(
            --cov=src
            --cov-report=xml:"$COVERAGE_XML"
            --cov-fail-under=60
        )
    else
        PYTEST_ARGS+=(--no-cov)
    fi

    if [[ "$INCLUDE_SLOW" -eq 1 ]]; then
        PYTEST_ARGS+=(-m "")
    fi

    if "$PYTHON_BIN" -m pytest --help | grep -q -- "--timeout"; then
        PYTEST_ARGS+=(--timeout=300)
    fi

    if [[ "${#PYTEST_EXTRA_ARGS[@]}" -gt 0 ]]; then
        "$PYTHON_BIN" -m pytest "${PYTEST_ARGS[@]}" "${PYTEST_EXTRA_ARGS[@]}"
    else
        "$PYTHON_BIN" -m pytest "${PYTEST_ARGS[@]}"
    fi

    if [[ "$RUN_LIVE_API" -eq 1 ]]; then
        start_live_api_if_needed
        LIVE_PYTEST_ARGS=(
            "${LIVE_TEST_PATHS[@]}"
            -n 0
            --no-cov
            --junitxml="$LIVE_JUNIT_XML"
        )
        if "$PYTHON_BIN" -m pytest --help | grep -q -- "--timeout"; then
            LIVE_PYTEST_ARGS+=(--timeout=300)
        fi
        NRG_REQUIRE_LIVE_API=1 \
        NRG_AUDIT_DIR="$LIVE_API_AUDIT_DIR" \
        NRG_BASE_URL="$LIVE_API_BASE" \
        API_URL="$LIVE_API_BASE" \
        NRG_API_URL="$LIVE_API_BASE" \
        "$PYTHON_BIN" -m pytest "${LIVE_PYTEST_ARGS[@]}"
    fi
}
ELAPSED_SECONDS=$((SECONDS - START_SECONDS))

"$PYTHON_BIN" scripts/check_test_runtime_budget.py \
    --runtime-seconds "$ELAPSED_SECONDS" \
    --baseline-seconds "${TEST_RUNTIME_BASELINE_SECONDS:-250}" \
    --max-growth "${TEST_RUNTIME_MAX_GROWTH:-0.20}" \
    --absolute-max-seconds "${TEST_RUNTIME_MAX_SECONDS:-300}"

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  Results"
echo "  JUnit XML:    $JUNIT_XML"
if [[ "$WITH_COVERAGE" -eq 1 ]]; then
    echo "  Coverage XML: $COVERAGE_XML"
else
    echo "  Coverage XML: skipped (--coverage not set)"
fi
echo "═══════════════════════════════════════════════════════"
