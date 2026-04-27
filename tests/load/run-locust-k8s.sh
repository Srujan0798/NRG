#!/usr/bin/env bash
# NRG C4 Load Test — K8s Runner
# Usage: ./run-locust-k8s.sh [staging|production]

set -euo pipefail

ENVIRONMENT="${1:-staging}"
NAMESPACE="nrg-loadtest"
JOB_NAME="nrg-c4-load-test"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
EVIDENCE_DIR="evidence/$(date +%Y-%m-%d)/C4_1000_user_locust"

echo "═══════════════════════════════════════════════════════════"
echo "  NRG C4 Load Test — K8s Deployment"
echo "  Environment: $ENVIRONMENT"
echo "  Timestamp:   $TIMESTAMP"
echo "═══════════════════════════════════════════════════════════"

# ── Preconditions ─────────────────────────────────────────
echo ""
echo "[1/6] Checking prerequisites..."

if ! command -v kubectl &> /dev/null; then
    echo "ERROR: kubectl not found"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "ERROR: docker not found"
    exit 1
fi

# Verify cluster connectivity
if ! kubectl cluster-info &> /dev/null; then
    echo "ERROR: Cannot connect to K8s cluster"
    exit 1
fi

echo "  ✓ kubectl available"
echo "  ✓ docker available"
echo "  ✓ cluster connected"

# ── Build Locust image ────────────────────────────────────
echo ""
echo "[2/6] Building Locust image..."
docker build -f tests/load/Dockerfile.locust -t "nrg-locust:c4-${TIMESTAMP}" tests/load/
echo "  ✓ Image built: nrg-locust:c4-${TIMESTAMP}"

# ── Apply K8s resources ───────────────────────────────────
echo ""
echo "[3/6] Applying K8s resources..."
kubectl apply -f tests/load/k8s-locust-job.yaml

# Patch job with current image tag
kubectl set image job/${JOB_NAME} locust-master="nrg-locust:c4-${TIMESTAMP}" -n ${NAMESPACE}

echo "  ✓ Namespace: ${NAMESPACE}"
echo "  ✓ Job: ${JOB_NAME}"

# ── Wait for completion ───────────────────────────────────
echo ""
echo "[4/6] Waiting for load test to complete..."
echo "  (This will take ~17 minutes)"
kubectl wait --for=condition=complete --timeout=30m job/${JOB_NAME} -n ${NAMESPACE}
echo "  ✓ Job completed"

# ── Collect evidence ──────────────────────────────────────
echo ""
echo "[5/6] Collecting evidence..."
mkdir -p "${EVIDENCE_DIR}"

# Get pod name
POD_NAME=$(kubectl get pods -n ${NAMESPACE} -l app=${JOB_NAME} --field-selector=status.phase=Succeeded -o jsonpath='{.items[0].metadata.name}')

# Copy reports from pod
kubectl cp "${NAMESPACE}/${POD_NAME}:/mnt/locust/report.html" "${EVIDENCE_DIR}/report_${TIMESTAMP}.html"
kubectl cp "${NAMESPACE}/${POD_NAME}:/mnt/locust/nrg-c4_stats.csv" "${EVIDENCE_DIR}/stats_${TIMESTAMP}.csv"
kubectl cp "${NAMESPACE}/${POD_NAME}:/mnt/locust/nrg-c4_failures.csv" "${EVIDENCE_DIR}/failures_${TIMESTAMP}.csv" 2>/dev/null || true

# Capture pod logs
kubectl logs "${POD_NAME}" -n ${NAMESPACE} > "${EVIDENCE_DIR}/logs_${TIMESTAMP}.txt"

# Capture cluster metrics during test
kubectl top nodes > "${EVIDENCE_DIR}/node_metrics_${TIMESTAMP}.txt" 2>/dev/null || echo "(metrics-server not available)" > "${EVIDENCE_DIR}/node_metrics_${TIMESTAMP}.txt"

echo "  ✓ Report: ${EVIDENCE_DIR}/report_${TIMESTAMP}.html"
echo "  ✓ Stats:  ${EVIDENCE_DIR}/stats_${TIMESTAMP}.csv"
echo "  ✓ Logs:   ${EVIDENCE_DIR}/logs_${TIMESTAMP}.txt"

# ── Cleanup ───────────────────────────────────────────────
echo ""
echo "[6/6] Cleanup..."
kubectl delete job ${JOB_NAME} -n ${NAMESPACE} --wait=false
echo "  ✓ Job deleted (pod will be garbage collected)"

# ── Summary ───────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  C4 Load Test Complete"
echo "  Evidence: ${EVIDENCE_DIR}/"
echo "═══════════════════════════════════════════════════════════"

# Quick pass/fail from logs
if grep -q "C4 PASS" "${EVIDENCE_DIR}/logs_${TIMESTAMP}.txt" 2>/dev/null; then
    echo "  ✅ C4 PASS"
    exit 0
elif grep -q "C4 FAIL" "${EVIDENCE_DIR}/logs_${TIMESTAMP}.txt" 2>/dev/null; then
    echo "  ❌ C4 FAIL — review logs"
    exit 1
else
    echo "  ⚠️  Result unclear — review logs manually"
    exit 2
fi
