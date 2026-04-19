# Runbook: Qdrant Down

## Alert
`up{job="qdrant"} == 0` for > 5 minutes

## Severity
CRITICAL

## Symptoms
- RAG queries fail
- `/health/qdrant` returns unhealthy
- Vector similarity search unavailable

## Verification

```bash
# Check Qdrant health
curl http://localhost:6333/readyz

# Check logs
kubectl -n nrg logs statefulset/qdrant --tail=100

# Check resource usage
kubectl -n nrg top pod -l app=qdrant
```

## Mitigation

### Quick restart:

```bash
# Rolling restart
kubectl -n ngr rollout restart statefulset/qdrant

# Wait for recovery
kubectl -n nrg rollout status statefulset/qdrant
```

### If persistent issues:

```bash
# Check disk space
df -h /qdrant/storage

# Check for corruption
kubectl -n nrg exec qdrant-0 -- ls -la /qdrant/storage

# Scale up if needed
kubectl -n nrg scale statefulset/qdrant --replicas=3
```

## Rollback

If data corruption suspected:

```bash
# Restore from snapshot
curl -X POST \
  http://localhost:6333/collections/nrg_research_tier1/snapshots/recover \
  -H "Content-Type: application/json" \
  -d '{"snapshot_location": "/qdrant/snapshots/latest.snapshot"}'
```

## Owner
DevOps Team (devops@nrg.india)

## Related Dashboards
- Vector Store Health: http://grafana/d/qdrant-health
- RAG Performance: http://grafana/d/rag-metrics
