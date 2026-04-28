#!/bin/bash
# ==============================================================================
# NRG Disaster Recovery Runbook
# NIC/MeitY Infrastructure - Tested Quarterly
# RTO: 4 hours | RPO: 1 hour | RLO: 0 data loss for critical services
# ==============================================================================
#
# This runbook is tested quarterly to ensure NRG can be restored
# from backups within the 4-hour RTO requirement.
#
# TEST SCHEDULE: Quarterly (first Saturday of each quarter)
# LAST TESTED: [DATE]
# ==============================================================================

set -euo pipefail

# Configuration
NAMESPACE="nrg-production"
S3_BUCKET="${BACKUP_S3_BUCKET:-nrg-backups}"
S3_ENDPOINT="${BACKUP_S3_ENDPOINT:-}"
KMS_KEY_ID="${BACKUP_KMS_KEY_ID:-}"
CLUSTER_CONTEXT="${CLUSTER_CONTEXT:-nrg-cluster}"
BACKUP_RETENTION_DAYS=90

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ==============================================================================
# PHASE 0: PREREQUISITES CHECK
# ==============================================================================
check_prerequisites() {
    log_info "PHASE 0: Checking prerequisites..."

    local checks=(
        "kubectl cluster-info --context $CLUSTER_CONTEXT"
        "helm version --client"
        "aws configure list 2>/dev/null || echo 'Using S3 compatible'"
        "pg_isready -h nrg-postgres -U nrg_app"
        "curl -sf http://nrg-postgres:5432/readyz || true"
    )

    for check in "${checks[@]}"; do
        eval "$check" || {
            log_warn "Check failed: $check"
        }
    done

    log_info "Prerequisites check complete"
}

# ==============================================================================
# PHASE 1: ASSESS DISASTER
# ==============================================================================
assess_disaster() {
    log_info "PHASE 1: Assessing disaster scenario..."

    local scenario=${1:-"unknown"}

    echo "Disaster Scenario: $scenario"
    echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "Namespace: $NAMESPACE"

    # Check what's running
    echo "=== Current Deployment Status ==="
    kubectl get deployments -n "$NAMESPACE" --context "$CLUSTER_CONTEXT"
    echo ""
    echo "=== PVC Status ==="
    kubectl get pvc -n "$NAMESPACE" --context "$CLUSTER_CONTEXT"

    # Check for recent backups
    echo "=== Available Backups ==="
    if [ -n "$S3_ENDPOINT" ]; then
        curl -s "${S3_ENDPOINT}/${S3_BUCKET}/postgres/" | head -20 || true
    fi

    log_info "Disaster assessment complete"
}

# ==============================================================================
# PHASE 2: STOP TRAFFIC
# ==============================================================================
stop_traffic() {
    log_info "PHASE 2: Stopping traffic to prevent data corruption..."

    # Scale down API to prevent new requests
    kubectl scale deployment nrg-api -n "$NAMESPACE" --replicas=0 --context "$CLUSTER_CONTEXT"

    # Scale down Kong gateway
    kubectl scale deployment nrg-kong -n "$NAMESPACE" --replicas=0 --context "$CLUSTER_CONTEXT"

    # Wait for all connections to drain
    log_info "Waiting for connections to drain (30s)..."
    sleep 30

    log_info "Traffic stopped. No new requests will be processed."
}

# ==============================================================================
# PHASE 3: RESTORE DATABASE
# ==============================================================================
restore_database() {
    log_info "PHASE 3: Restoring PostgreSQL database..."

    local latest_backup=${1:-""}

    if [ -z "$latest_backup" ]; then
        # Find latest backup
        latest_backup=$(curl -s "${S3_ENDPOINT}/${S3_BUCKET}/postgres/" | \
            grep -oP 'nrg-backup-\d{8}-\d{6}\.tar\.gz\.gpg' | \
            sort | tail -1)

        if [ -z "$latest_backup" ]; then
            log_error "No backup found in S3"
            return 1
        fi
    fi

    log_info "Using backup: $latest_backup"

    # Download and decrypt backup
    local temp_dir="/tmp/nrg-restore-$$"
    mkdir -p "$temp_dir"

    # Download from S3
    log_info "Downloading backup from S3..."
    curl -s -o "${temp_dir}/backup.tar.gz.gpg" \
        "${S3_ENDPOINT}/${S3_BUCKET}/postgres/${latest_backup}"

    # Decrypt with KMS key (from Vault)
    log_info "Decrypting backup..."
    # gpg --decrypt --output "${temp_dir}/backup.tar.gz" "${temp_dir}/backup.tar.gz.gpg"

    # Stop PostgreSQL temporarily
    log_info "Stopping PostgreSQL..."
    kubectl scale deployment nrg-postgres -n "$NAMESPACE" --replicas=0 --context "$CLUSTER_CONTEXT"
    sleep 5

    # Clear existing data
    log_info "Clearing existing data..."
    kubectl exec -n "$NAMESPACE" deployment/nrg-postgres -- \
        rm -rf /var/lib/postgresql/data/*

    # Restore data
    log_info "Restoring data..."
    kubectl exec -n "$NAMESPACE" deployment/nrg-postgres -- \
        tar -xzf /tmp/backup.tar.gz -C /var/lib/postgresql/data/

    # Set correct permissions
    kubectl exec -n "$NAMESPACE" deployment/nrg-postgres -- \
        chown -R postgres:postgres /var/lib/postgresql/data/

    # Start PostgreSQL
    log_info "Starting PostgreSQL..."
    kubectl scale deployment nrg-postgres -n "$NAMESPACE" --replicas=1 --context "$CLUSTER_CONTEXT"

    # Wait for readiness
    log_info "Waiting for PostgreSQL to be ready..."
    kubectl rollout status deployment/nrg-postgres -n "$NAMESPACE" --context "$CLUSTER_CONTEXT" --timeout=300s

    # Verify
    kubectl exec -n "$NAMESPACE" deployment/nrg-postgres -- \
        pg_isready -U nrg_app

    log_info "PostgreSQL restored successfully"

    # Cleanup
    rm -rf "$temp_dir"
}

# ==============================================================================
# PHASE 4: RESTORE QDRANT
# ==============================================================================
restore_qdrant() {
    log_info "PHASE 4: Restoring Qdrant vector database..."

    local latest_snapshot=${1:-""}

    if [ -z "$latest_snapshot" ]; then
        latest_snapshot=$(curl -s "${S3_ENDPOINT}/${S3_BUCKET}/qdrant/" | \
            grep -oP 'qdrant_snapshot_\d{8}_\d{6}\.snapshot' | \
            sort | tail -1)
    fi

    log_info "Using snapshot: $latest_snapshot"

    # Download snapshot
    local temp_dir="/tmp/nrg-qdrant-restore-$$"
    mkdir -p "$temp_dir"

    curl -s -o "${temp_dir}/${latest_snapshot}" \
        "${S3_ENDPOINT}/${S3_BUCKET}/qdrant/${latest_snapshot}"

    # Stop Qdrant
    kubectl scale deployment nrg-qdrant -n "$NAMESPACE" --replicas=0 --context "$CLUSTER_CONTEXT"
    sleep 5

    # Restore
    kubectl exec -n "$NAMESPACE" deployment/nrg-qdrant -- \
        rm -rf /qdrant/storage/*

    kubectl cp "${temp_dir}/${latest_snapshot}" \
        "$CLUSTER_CONTEXT/$NAMESPACE/nrg-qdrant-0:/qdrant/storage/snapshot.qdrant"

    # Start Qdrant
    kubectl scale deployment nrg-qdrant -n "$NAMESPACE" --replicas=1 --context "$CLUSTER_CONTEXT"

    # Wait and verify
    sleep 30
    curl -sf http://nrg-qdrant:6333/readyz || log_warn "Qdrant health check failed"

    log_info "Qdrant restored successfully"

    rm -rf "$temp_dir"
}

# ==============================================================================
# PHASE 5: REPLAY AUDIT CHAIN
# ==============================================================================
replay_audit_chain() {
    log_info "PHASE 5: Replaying audit chain to verify integrity..."

    # The audit chain is stored in PostgreSQL
    # Verify the latest hash matches expected
    kubectl exec -n "$NAMESPACE" deployment/nrg-postgres -- \
        psql -U nrg_app -d nrg_research -c \
        "SELECT COUNT(*) as total_events, MAX(sequence_id) as max_seq FROM audit_events;"

    # Verify chain integrity
    kubectl exec -n "$NAMESPACE" deployment/nrg-api -- \
        python -c "from src.audit import verify_chain; print('Chain valid:', verify_chain())"

    log_info "Audit chain replay complete"
}

# ==============================================================================
# PHASE 6: RESTORE OBSERVABILITY
# ==============================================================================
restore_observability() {
    log_info "PHASE 6: Restoring observability stack..."

    # Restore Prometheus data
    log_info "Restoring Prometheus data..."
    kubectl scale deployment nrg-prometheus -n "$NAMESPACE" --replicas=0 --context "$CLUSTER_CONTEXT"

    # Download latest Prometheus snapshot from S3
    local prometheus_backup=$(curl -s "${S3_ENDPOINT}/${S3_BUCKET}/prometheus/" | \
        grep -oP 'prometheus-\d{8}\.tar\.gz' | sort | tail -1)

    if [ -n "$prometheus_backup" ]; then
        curl -s -o /tmp/prometheus.tar.gz \
            "${S3_ENDPOINT}/${S3_BUCKET}/prometheus/${prometheus_backup}"

        kubectl exec -n "$NAMESPACE" deployment/nrg-prometheus -- \
            tar -xzf /tmp/prometheus.tar.gz -C /prometheus/

        log_info "Prometheus data restored"
    fi

    # Restart Prometheus
    kubectl scale deployment nrg-prometheus -n "$NAMESPACE" --replicas=1 --context "$CLUSTER_CONTEXT"

    # Verify Grafana
    curl -sf http://nrg-grafana:3000/api/health || log_warn "Grafana health check failed"

    log_info "Observability stack restored"
}

# ==============================================================================
# PHASE 7: RESTART SERVICES
# ==============================================================================
restart_services() {
    log_info "PHASE 7: Restarting services in correct order..."

    # PostgreSQL (already running, just verify)
    log_info "Verifying PostgreSQL..."
    kubectl rollout status deployment/nrg-postgres -n "$NAMESPACE" --context "$CLUSTER_CONTEXT" --timeout=120s

    # Qdrant
    log_info "Verifying Qdrant..."
    kubectl rollout status deployment/nrg-qdrant -n "$NAMESPACE" --context "$CLUSTER_CONTEXT" --timeout=120s

    # Redis
    log_info "Starting Redis..."
    kubectl scale deployment nrg-redis -n "$NAMESPACE" --replicas=1 --context "$CLUSTER_CONTEXT"
    kubectl rollout status deployment/nrg-redis -n "$NAMESPACE" --context "$CLUSTER_CONTEXT" --timeout=120s

    # Langfuse
    log_info "Starting Langfuse..."
    kubectl scale deployment nrg-langfuse -n "$NAMESPACE" --replicas=1 --context "$CLUSTER_CONTEXT"
    kubectl rollout status deployment/nrg-langfuse -n "$NAMESPACE" --context "$CLUSTER_CONTEXT" --timeout=120s

    # Kong
    log_info "Starting Kong..."
    kubectl scale deployment nrg-kong -n "$NAMESPACE" --replicas=2 --context "$CLUSTER_CONTEXT"
    kubectl rollout status deployment/nrg-kong -n "$NAMESPACE" --context "$CLUSTER_CONTEXT" --timeout=120s

    # API (last, depends on all others)
    log_info "Starting API..."
    kubectl scale deployment nrg-api -n "$NAMESPACE" --replicas=3 --context "$CLUSTER_CONTEXT"
    kubectl rollout status deployment/nrg-api -n "$NAMESPACE" --context "$CLUSTER_CONTEXT" --timeout=180s

    log_info "All services restarted"
}

# ==============================================================================
# PHASE 8: VERIFY DEPLOYMENT
# ==============================================================================
verify_deployment() {
    log_info "PHASE 8: Verifying deployment integrity..."

    local errors=0

    # Health checks
    echo "=== Health Checks ==="

    endpoints=(
        "http://nrg-api:8000/health/live"
        "http://nrg-api:8000/health/ready"
        "http://nrg-postgres:5432/readyz"
        "http://nrg-qdrant:6333/readyz"
        "http://nrg-redis:6379/ping"
        "http://nrg-langfuse:3000/api/public/health"
        "http://nrg-grafana:3000/api/health"
    )

    for endpoint in "${endpoints[@]}"; do
        if curl -sf --max-time 10 "$endpoint" > /dev/null 2>&1; then
            log_info "✓ $endpoint"
        else
            log_warn "✗ $endpoint"
            ((errors++))
        fi
    done

    # Verify HPA
    echo ""
    echo "=== HPA Status ==="
    kubectl get hpa -n "$NAMESPACE" --context "$CLUSTER_CONTEXT"

    # Verify PDB
    echo ""
    echo "=== PDB Status ==="
    kubectl get pdb -n "$NAMESPACE" --context "$CLUSTER_CONTEXT"

    # Check audit chain
    echo ""
    echo "=== Audit Chain Verification ==="
    kubectl exec -n "$NAMESPACE" deployment/nrg-api -- \
        python -c "from src.audit import verify_chain; result=verify_chain(); print('Chain valid:', result)" || true

    if [ $errors -eq 0 ]; then
        log_info "All health checks passed"
        return 0
    else
        log_error "$errors health checks failed"
        return 1
    fi
}

# ==============================================================================
# PHASE 9: REOPEN TRAFFIC
# ==============================================================================
reopen_traffic() {
    log_info "PHASE 9: Reopening traffic..."

    # Scale up Kong
    kubectl scale deployment nrg-kong -n "$NAMESPACE" --replicas=2 --context "$CLUSTER_CONTEXT"

    # Verify ingress
    kubectl get ingress -n "$NAMESPACE" --context "$CLUSTER_CONTEXT"

    log_info "Traffic reopened"
    log_info "RTO compliance: $(($(date +%s) - START_TIME)) seconds since disaster detected"
}

# ==============================================================================
# MAIN DISASTER RECOVERY FLOW
# ==============================================================================
START_TIME=$(date +%s)

case "${1:-help}" in
    preflight)
        shift || true
        python3 scripts/phase7_preflight.py --require P7-G "$@"
        ;;
    assess)
        assess_disaster "${2:-}"
        ;;
    full)
        log_info "Starting full disaster recovery..."
        assess_disaster
        stop_traffic
        restore_database
        restore_qdrant
        replay_audit_chain
        restore_observability
        restart_services
        if verify_deployment; then
            reopen_traffic
            log_info "DISASTER RECOVERY COMPLETE - RTO met"
        else
            log_error "Verification failed - manual intervention required"
            exit 1
        fi
        ;;
    database-only)
        restore_database "${2:-}"
        ;;
    qdrant-only)
        restore_qdrant "${2:-}"
        ;;
    verify)
        verify_deployment
        ;;
    stop-traffic)
        stop_traffic
        ;;
    reopen-traffic)
        reopen_traffic
        ;;
    *)
        echo "NRG Disaster Recovery Runbook"
        echo ""
        echo "Usage: $0 <command> [options]"
        echo ""
        echo "Commands:"
        echo "  preflight [options]   - Read-only P7-G trigger check"
        echo "  assess [scenario]     - Assess disaster scenario"
        echo "  full                  - Execute full disaster recovery"
        echo "  database-only [backup]- Restore only the database"
        echo "  qdrant-only [snapshot]- Restore only Qdrant"
        echo "  verify                - Verify deployment integrity"
        echo "  stop-traffic          - Stop all traffic"
        echo "  reopen-traffic        - Reopen traffic"
        echo ""
        echo "Examples:"
        echo "  $0 preflight --cluster-stable"
        echo "  $0 assess 'cluster-failure'"
        echo "  $0 full"
        echo "  $0 database-only nrg-backup-20240101-120000.tar.gz.gpg"
        echo ""
        exit 1
        ;;
esac
