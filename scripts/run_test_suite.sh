#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-.venv/bin/python}"
EVIDENCE_DIR="${EVIDENCE_DIR:-evidence/2026-04-26}"
JUNIT_XML="${JUNIT_XML:-$EVIDENCE_DIR/test_suite_full.xml}"
LOG_FILE="${LOG_FILE:-$EVIDENCE_DIR/test_suite_full.log}"
MAX_FAST_SECONDS="${MAX_FAST_SECONDS:-900}"
MAX_SLOW_SECONDS="${MAX_SLOW_SECONDS:-1800}"
MAX_UNMARKED_TEST_SECONDS="${MAX_UNMARKED_TEST_SECONDS:-30}"

usage() {
  cat <<'USAGE'
Usage: scripts/run_test_suite.sh [--fast|--slow|--check-slow-markers]

Runs the LB-4 test-suite gate and writes JUnit evidence.

Modes:
  --fast                 Run the sub-15-minute non-slow suite. Default.
  --slow                 Run only tests marked slow.
  --check-slow-markers   Run the non-slow suite and fail if any test call
                         exceeds 30s without the slow marker.

Environment:
  PYTHON_BIN                 Python executable. Default: .venv/bin/python
  JUNIT_XML                  JUnit XML path. Default: evidence/2026-04-26/test_suite_full.xml
  MAX_FAST_SECONDS           Fast-suite wall-clock budget. Default: 900
  MAX_SLOW_SECONDS           Slow-suite wall-clock budget. Default: 1800
  MAX_UNMARKED_TEST_SECONDS  Per-test slow-marker threshold. Default: 30
  NRG_TEST_DATABASE_URL      Database URL for this local gate.
                            Default: sqlite:///<repo>/nrg_research.db
  PYTEST_WORKERS             xdist worker count. Default: auto. Use 0 to disable.
USAGE
}

mode="fast"
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
elif [[ "${1:-}" == "--slow" ]]; then
  mode="slow"
elif [[ "${1:-}" == "--check-slow-markers" ]]; then
  mode="check-slow-markers"
elif [[ "${1:-}" == "--fast" || -z "${1:-}" ]]; then
  mode="fast"
else
  usage >&2
  exit 2
fi

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Python executable not found or not executable: $PYTHON_BIN" >&2
  exit 2
fi

export ROUTER_ENABLE_2STAGE="${ROUTER_ENABLE_2STAGE:-false}"
export DATABASE_URL="${NRG_TEST_DATABASE_URL:-sqlite:///$ROOT_DIR/nrg_research.db}"

mkdir -p "$EVIDENCE_DIR"

pytest_args=(
  -o "addopts="
  -m "not slow"
  --tb=short
  --junitxml "$JUNIT_XML"
  --durations=0
  --durations-min="$MAX_UNMARKED_TEST_SECONDS"
)

if [[ "${PYTEST_WORKERS:-auto}" != "0" ]] && "$PYTHON_BIN" -c "import xdist" >/dev/null 2>&1; then
  pytest_args=(-n "${PYTEST_WORKERS:-auto}" "${pytest_args[@]}")
fi

if "$PYTHON_BIN" -c "import pytest_rerunfailures" >/dev/null 2>&1; then
  pytest_args=(--reruns 1 --reruns-delay 1 "${pytest_args[@]}")
fi

if [[ "$mode" == "slow" ]]; then
  JUNIT_XML="${JUNIT_XML%.xml}_slow.xml"
  LOG_FILE="${LOG_FILE%.log}_slow.log"
  pytest_args=(-o "addopts=" -m "slow" --tb=short --junitxml "$JUNIT_XML" --durations=25)
  if [[ "${PYTEST_WORKERS:-auto}" != "0" ]] && "$PYTHON_BIN" -c "import xdist" >/dev/null 2>&1; then
    pytest_args=(-n "${PYTEST_WORKERS:-auto}" --dist=loadscope "${pytest_args[@]}")
  fi
  if "$PYTHON_BIN" -c "import pytest_rerunfailures" >/dev/null 2>&1; then
    pytest_args=(--reruns 1 --reruns-delay 1 "${pytest_args[@]}")
  fi
fi

start_epoch="$(date +%s)"
set +e
"$PYTHON_BIN" -m pytest tests "${pytest_args[@]}" 2>&1 | tee "$LOG_FILE"
pytest_status="${PIPESTATUS[0]}"
set -e
end_epoch="$(date +%s)"
elapsed_seconds="$((end_epoch - start_epoch))"

if [[ "$mode" != "slow" ]]; then
  set +e
  "$PYTHON_BIN" - "$LOG_FILE" "$MAX_UNMARKED_TEST_SECONDS" <<'PY'
import re
import sys
from pathlib import Path

log_path = Path(sys.argv[1])
threshold = float(sys.argv[2])
pattern = re.compile(r"^\s*(?P<seconds>\d+(?:\.\d+)?)s\s+call\s+(?P<nodeid>tests/.+)$")

violations = []
for line in log_path.read_text(errors="replace").splitlines():
    match = pattern.match(line)
    if not match:
        continue
    seconds = float(match.group("seconds"))
    if seconds > threshold:
        violations.append((seconds, match.group("nodeid")))

if violations:
    print("\nUnmarked slow tests detected:")
    for seconds, nodeid in violations:
        print(f"  {seconds:.2f}s {nodeid}")
    print("Add @pytest.mark.slow or reduce runtime before this gate can pass.")
    sys.exit(1)
PY
  duration_status="$?"
  set -e
else
  duration_status=0
fi

if [[ "$mode" != "slow" && "$elapsed_seconds" -gt "$MAX_FAST_SECONDS" ]]; then
  echo "Fast suite exceeded ${MAX_FAST_SECONDS}s budget: ${elapsed_seconds}s" >&2
  duration_status=1
fi

if [[ "$mode" == "slow" && "$elapsed_seconds" -gt "$MAX_SLOW_SECONDS" ]]; then
  echo "Slow suite exceeded ${MAX_SLOW_SECONDS}s budget: ${elapsed_seconds}s" >&2
  duration_status=1
fi

echo "JUnit evidence: $JUNIT_XML"
echo "Log evidence: $LOG_FILE"
echo "Elapsed seconds: $elapsed_seconds"

if [[ "$pytest_status" -ne 0 ]]; then
  exit "$pytest_status"
fi
exit "$duration_status"
