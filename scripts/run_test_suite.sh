#!/usr/bin/env bash
# LB-4: Run full pytest suite with parallel execution and JUnit output.
# Target: <5 minutes for the default non-slow suite on an 8-core machine.
# Usage: ./scripts/run_test_suite.sh [--coverage] [--slow] [evidence_dir] [pytest args...]

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WITH_COVERAGE=0
INCLUDE_SLOW=0
PYTEST_EXTRA_ARGS=()
EVIDENCE_DIR=""

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

JUNIT_XML="$EVIDENCE_DIR/test_suite_full_final.xml"
COVERAGE_XML="$EVIDENCE_DIR/coverage.xml"
PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "═══════════════════════════════════════════════════════"
echo "  NRG Full Test Suite"
echo "  Evidence dir: $EVIDENCE_DIR"
echo "  JUnit XML:    $JUNIT_XML"
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

    "$PYTHON_BIN" -m pytest "${PYTEST_ARGS[@]}" "${PYTEST_EXTRA_ARGS[@]}"
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
