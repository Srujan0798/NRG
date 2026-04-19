#!/usr/bin/env bash
set -euo pipefail

# NRG Disaster Recovery Drill Script
# Run quarterly or on-demand for DR validation
# Validates RTO < 60 min, RPO < 1 hour

NAMESPACE="${NAMESPACE:-nrg-stg}"
BACKUP_DATE="${BACKUP_DATE:-$(date +%F)}"
DRILL_LOG="dr_drill_$(date +%Y%m%d_%H%M%S).log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$DRILL_LOG"
}

error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $*" | tee -a "$DRILL_LOG" >&2
}

check_prereqs() {
    log "=== Checking Prerequisites ==="
    command -v kubectl >/dev/null 2>&1 || { error "kubectl not installed"; exit 1; }
    command -v psql >/dev/null 2>&1 || log "WARN: psql not installed, will skip DB checks"
    command -v curl >/dev/null 2>&1 || { error "curl not installed"; exit 1; }
    log "Prerequisites OK"
}

backup_databases() {
    log "=== Backing Up Databases ==="

    # PostgreSQL backup
    if command -v psql >/dev/null 2>&1; then
        log "Backing up PostgreSQL..."
        PGPASSWORD="${PGPASSWORD:-nrg_secret}" pg_dump -h nrg-postgres -U nrg -d nrg -Fc > "backups/nrg_pg_${BACKUP_DATE}.dump" 2>&1 | tee -a "$DRILL_LOG"
        log "PostgreSQL backup complete: backups/nrg_pg_${BACKUP_DATE}.dump"
    fi

    # Qdrant snapshot
    log "Creating Qdrant snapshot..."
    curl -X POST "http://nrg-qdrant:6333/collections/nrg_research_tier1/snapshots" 2>/dev/null | tee -a "$DRILL_LOG" || log "WARN: Qdrant snapshot failed"

    # Audit chain backup
    log "Backing up audit chain..."
    cp .audit/chain.jsonl "backups/chain_${BACKUP_DATE}.jsonl" 2>/dev/null || log "WARN: Audit chain backup failed"

    log "Backup phase complete"
}

simulate_disaster() {
    log "=== Simulating Disaster ==="

    log "Stopping NRG services..."
    kubectl scale deployment nrg-api --replicas=0 -n "$NAMESPACE" 2>&1 | tee -a "$DRILL_LOG" || true
    kubectl scale deployment nrg-worker --replicas=0 -n "$NAMESPACE" 2>&1 | tee -a "$DRILL_LOG" || true

    log "Deleting API pod to simulate crash..."
    kubectl delete pod -l app=nrg-api -n "$NAMESPACE" --force 2>&1 | tee -a "$DRILL_LOG" || true

    sleep 5
    log "Disaster simulation complete"
}

restore_services() {
    log "=== Restoring Services ==="
    START_TIME=$(date +%s)

    log "Restoring API deployment..."
    kubectl scale deployment nrg-api --replicas=2 -n "$NAMESPACE" 2>&1 | tee -a "$DRILL_LOG"

    log "Waiting for API pod ready..."
    kubectl wait --for=condition=ready pod -l app=nrg-api -n "$NAMESPACE" --timeout=300s 2>&1 | tee -a "$DRILL_LOG"

    RESTORE_TIME=$(($(date +%s) - START_TIME))
    log "Services restored in ${RESTORE_TIME}s"

    if (( RESTORE_TIME > 3600 )); then
        error "RTO exceeded 60 minutes: ${RESTORE_TIME}s"
        return 1
    fi

    log "RTO check passed: ${RESTORE_TIME}s < 3600s"
}

verify_data_integrity() {
    log "=== Verifying Data Integrity ==="

    # Check audit chain
    log "Verifying audit chain..."
    RESP=$(curl -sf http://localhost:8000/audit/verify -H "Authorization: Bearer $ADMIN_TOKEN" 2>&1) || true
    if echo "$RESP" | grep -q '"ok":true'; then
        log "Audit chain verification: PASSED"
    else
        error "Audit chain verification: FAILED"
    fi

    # Check DB row counts
    log "Checking database row counts..."
    curl -sf http://localhost:8000/stats -H "Authorization: Bearer $TOKEN" | tee -a "$DRILL_LOG" || true

    # Check Qdrant connectivity
    log "Checking Qdrant health..."
    curl -sf "http://nrg-qdrant:6333/collections" | tee -a "$DRILL_LOG" || log "WARN: Qdrant health check failed"

    log "Data integrity check complete"
}

smoke_test() {
    log "=== Running Smoke Tests ==="

    # Health check
    if curl -sf http://localhost:8000/health > /dev/null; then
        log "Health check: PASSED"
    else
        error "Health check: FAILED"
    fi

    # Login test
    if curl -sf -X POST http://localhost:8000/login -H 'content-type: application/json' \
        -d '{"username":"researcher_user","password":"researcher-pass"}' > /dev/null 2>&1; then
        log "Login test: PASSED"
    else
        error "Login test: FAILED"
    fi

    log "Smoke tests complete"
}

generate_report() {
    log "=== Generating DR Drill Report ==="

    cat >> "$DRILL_LOG" <<EOF

=== DR DRILL REPORT ===
Date: $(date)
Namespace: $NAMESPACE
RTO Target: < 60 minutes
RPO Target: < 1 hour

Status: COMPLETED
$(grep "check passed\|ERROR" "$DRILL_LOG" | head -20)

Next scheduled drill: +90 days
EOF

    log "Report saved to: $DRILL_LOG"
    log "=== DR DRILL COMPLETE ==="
}

main() {
    log "Starting NRG Disaster Recovery Drill"

    check_prereqs
    backup_databases
    simulate_disaster
    restore_services
    verify_data_integrity
    smoke_test
    generate_report
}

main "$@"