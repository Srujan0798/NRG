#!/usr/bin/env bash
# LB-4: Run full pytest suite with parallel execution, coverage, and JUnit output.
# Target: <15 minutes for all tests.
# Usage: ./scripts/run_test_suite.sh [evidence_dir]

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EVIDENCE_DIR="${1:-$REPO_ROOT/evidence/$(date +%Y-%m-%d)}"
mkdir -p "$EVIDENCE_DIR"

JUNIT_XML="$EVIDENCE_DIR/test_suite_full_final.xml"
COVERAGE_XML="$EVIDENCE_DIR/coverage.xml"

echo "═══════════════════════════════════════════════════════"
echo "  NRG Full Test Suite"
echo "  Evidence dir: $EVIDENCE_DIR"
echo "  JUnit XML:    $JUNIT_XML"
echo "═══════════════════════════════════════════════════════"

TIMEFORMAT='Suite completed in %R seconds'
time {
    cd "$REPO_ROOT"
    .venv/bin/python -m pytest tests/ \
        -n auto \
        --dist=loadgroup \
        --timeout=300 \
        --junitxml="$JUNIT_XML" \
        --cov=src \
        --cov-report=xml:"$COVERAGE_XML" \
        --cov-report=term-missing:skip-covered \
        --cov-fail-under=60 \
        "$@"
}

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  Results"
echo "  JUnit XML:    $JUNIT_XML"
echo "  Coverage XML: $COVERAGE_XML"
echo "═══════════════════════════════════════════════════════"
