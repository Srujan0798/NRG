# NRG Incident Response Playbook

## Overview

This playbook provides step-by-step procedures for handling incidents in the NRG (National Research Graph) platform.

---

## Incident Categories

### 1. LLM Provider Failure

**Alert:** `HighLLMErrorRate` - LLM error rate > 10% in 5 minutes  
**Severity:** Critical  
**Channel:** PagerDuty

#### Symptoms
- Query success rate drops below 90%
- LLM timeout errors in logs
- Fallback cascade activation

#### Response Procedure

```
1. IDENTIFY - Check which provider failed
   $ curl -s http://localhost:8000/health/llm | jq
   $ kubectl logs -n nrg -l app=nrg-api --tail=100 | grep -i "llm\|error"

2. VERIFY FALLBACK CHAIN - NVIDIA → Anthropic → Local
   $ curl -s http://localhost:8080/health | jq  # Local Llama.cpp
   $ kubectl get pods -n nrg | grep llama

3. IF LOCAL LLM DOWN
   $ kubectl rollout restart deployment/llama-cpp -n nrg
   $ kubectl logs -n nrg -l app=llama-cpp --tail=50

4. IF CLOUD LLM QUOTA EXCEEDED
   - Contact NVIDIA for limit increase
   - Temporarily switch: LLM_PROVIDER=local in .env
   - Monitor fallback rate in Grafana

5. NOTIFY USERS OF DEGRADED MODE
   - Post status update to #nrg-status
   - Set banner in UI if available

6. ESCALATE if not resolved in 15 minutes
   - Page on-call ML Platform engineer
```

---

### 2. Database Connection Exhaustion

**Alert:** `DBConnectionsHigh` - DB connections > 80%  
**Severity:** Warning  
**Channel:** Slack #nrg-alerts

#### Symptoms
- New queries timeout waiting for connection
- `sqlalchemy.pool.QueuePool` warnings in logs
- Slow query response times

#### Response Procedure

```
1. CHECK CONNECTION POOL STATUS
   $ curl -s http://localhost:8000/health/db | jq
   $ SELECT count(*) FROM pg_stat_activity WHERE state = 'active';

2. IDENTIFY BLOCKING QUERIES
   $ SELECT * FROM pg_stat_activity WHERE wait_event_type = 'Lock' LIMIT 10;

3. CHECK DISK SPACE
   $ df -h /var/lib/postgresql/data

4. IF REPLICA EXISTS - FAILOVER
   $ kubectl exec -it nrg-db-replica-0 -- patronictl switchover

5. SCALE CONNECTION POOL
   $ kubectl set env deployment/nrg-api DB_POOL_SIZE=20 -n nrg

6. CONTACT DBA if connections don't recover within 10 minutes
```

---

### 3. Query Latency Spike

**Alert:** `QueryLatencyHigh` - P95 latency > 30s  
**Severity:** Warning  
**Channel:** Slack #nrg-alerts

#### Diagnosis Flow

```
1. CHECK WHICH NODE IS SLOW
   Langfuse dashboard → Recent traces → Identify slow node
   Common culprits: RAG retrieval, LLM synthesis, SQL execution

2. CHECK QDRANT (RAG) LATENCY
   $ curl -s http://localhost:8000/health/qdrant | jq
   $ curl -s http://localhost:6333/collections | jq

3. CHECK DATABASE LATENCY
   $ curl -s http://localhost:8000/health/db | jq
   $ Check slow query log: kubectl exec -it nrg-api -- cat /logs/slow-query.log

4. CHECK LLM LATENCY
   Grafana → LLM Response Latency panel
   If LLM p95 > 10s → provider issue (see LLM Provider Failure)

5. IF QDRANT SLOW
   - Check collection size: kubectl exec -it nrg-qdrant -- curl localhost:6333/collections/nrg-research/stats
   - Reduce top_k in retrieval config
   - Consider index optimization

6. IF DB SLOW
   - Run ANALYZE on large tables
   - Check for missing indexes
   - Review query execution plans
```

---

### 4. Cache Hit Rate Degradation

**Alert:** `CacheHitRateLow` - Cache hit rate < 50%  
**Severity:** Info  
**Channel:** Slack #nrg-alerts

#### Investigation

```
1. CHECK REDIS HEALTH
   $ curl -s http://localhost:8000/health/redis | jq
   $ redis-cli info stats | grep hit_rate

2. CHECK CACHE SIZE
   $ redis-cli dbsize
   $ redis-cli info memory

3. WARM CACHE WITH COMMON QUERIES
   $ python scripts/warm_cache.py --queries-file common_queries.json

4. INCREASE CACHE TTL
   For /stats endpoint: 30s → 120s
   In src/caching/redis_layer.py

5. IF REDIS MEMORY PRESSURE
   $ redis-cli CONFIG SET maxmemory-policy allkeys-lru
   Or scale Redis pod: kubectl scale deployment nrg-redis --replicas=2
```

---

### 5. Qdrant Vector DB Down

**Alert:** `QdrantDown` - Qdrant unreachable for 5+ minutes  
**Severity:** Critical  
**Channel:** PagerDuty

#### Impact
- RAG retrieval fails
- Queries use text-only fallback
- Hallucination risk increases

#### Recovery Procedure

```
1. CHECK QDRANT POD STATUS
   $ kubectl get pods -n nrg | grep qdrant
   $ kubectl describe pod -n nrg -l app=qdrant

2. CHECK QDRANT LOGS
   $ kubectl logs -n nrg -l app=qdrant --tail=100

3. IF CrashLoopBackOff
   $ kubectl describe pod nrg-qdrant-0 | grep -A 5 "Last State"
   Common cause: disk full, OOM

4. IF DISK FULL
   $ kubectl exec -it nrg-qdrant-0 -- df -h
   Expand PVC: kubectl patch pvc nrg-qdrant-storage -n nrg -p '{"spec":{"resources":{"requests":{"storage":"50Gi"}}}}'

5. RESTART QDRANT
   $ kubectl rollout restart deployment/qdrant -n nrg

6. VERIFY RECOVERY
   $ curl -s http://localhost:6333/health | jq
   $ curl -s http://localhost:8000/health/qdrant | jq

7. RE-INGEST IF DATA CORRUPTION
   $ python scripts/re_ingest_qdrant.py --collection nrg-research
```

---

### 6. Audit Chain Integrity Failure

**Alert:** `AuditChainBroken` - nrg_audit_chain_ok = 0  
**Severity:** Critical  
**Channel:** PagerDuty + Security Team

#### Impact
- HMAC verification failing
- Potential tampering or data corruption
- Compliance violation risk

#### Investigation Procedure

```
1. IDENTIFY WHICH EVENT BROKE CHAIN
   $ curl -s http://localhost:8000/audit/verify -H "Authorization: Bearer $ADMIN_TOKEN" | jq

2. CHECK AUDIT LOGS
   $ kubectl logs -n nrg -l app=nrg-api --tail=500 | grep AUDIT

3. VERIFY DATABASE INTEGRITY
   $ psql -h localhost -U nrg -d nrg_db -c "SELECT * FROM audit_events ORDER BY created_at DESC LIMIT 10;"

4. IF MINOR (single event, no tampering)
   - Auto-seal next event to continue chain
   - Log incident in #nrg-security

5. IF TAMPERING SUSPECTED
   - PRESERVE all pod logs immediately
   - Stop all writes to audit log
   - Escalate to Security Team
   - Do NOT attempt self-healing

6. POST-INCIDENT
   - Document timeline in incident report
   - Review access logs for unauthorized modifications
   - Update security controls if needed
```

---

### 7. Prompt Injection Attack

**Alert:** `PromptInjectionSpike` - >10 injection attempts in 5 minutes  
**Severity:** Critical  
**Channel:** PagerDuty + Security Team

#### Response

```
1. IDENTIFY ATTACK PATTERNS
   $ kubectl logs -n nrg -l app=nrg-api --tail=200 | grep INJECTION
   $ kubectl logs -n nrg -l app=nrg-api --tail=200 | grep -i "ignore\|system\|admin"

2. IDENTIFY SOURCE IPS
   $ kubectl logs -n nrg -l app=nrg-api --tail=1000 | grep "source_ip"
   $ kubectl exec -it kong-xxx -n kong -- curl localhost:8001/logged_tokens | jq

3. BLOCK ATTACKER IPS
   At Kong gateway:
   $ kubectl exec -n kong deploy/kong -- kong config db_changed \
     --selector "source==$ATTACKER_IP" --ttl 3600

   Or at firewall level:
   $ iptables -A INPUT -s $ATTACKER_IP -j DROP

4. RATE LIMIT AFFECTED ROUTES
   $ kubectl patch gateway nrg-gateway -n nrg -p '{"spec":{"rateLimit":{"requestsPerMinute":10}}}'

5. REVIEW AND HARDEN PROMPT SANITIZER
   $ cat src/security/gateway/prompt_sanitiser.py
   Add new patterns to BLOCKED_PATTERNS

6. POST-INCIDENT
   - Document attack vectors in #nrg-security
   - Update WAF rules
   - Review if any attacks succeeded (check nrg_pii_block_total after attack window)
```

---

### 8. Egress Violation Detected

**Alert:** `EgressViolation` - Data sovereignty violation blocked  
**Severity:** Critical  
**Channel:** PagerDuty + Compliance Team

#### Investigation

```
1. IDENTIFY VIOLATION
   $ kubectl logs -n nrg -l app=nrg-api --tail=500 | grep EGRESS
   $ kubectl logs -n nrg -l app=nrg-egress-guard --tail=100

2. GET VIOLATION DETAILS
   - Source user and tier
   - Query that triggered violation
   - Destination that was blocked

3. VERIFY BLOCK WAS CORRECT
   Check if query was legitimate cross-border collaboration
   vs actual data exfiltration attempt

4. IF LEGITIMATE USE CASE
   - Document in ticket
   - Review egress rules for potential exceptions
   - Update allowed_destinations if needed

5. IF MALICIOUS
   - Block source user immediately
   - Preserve logs for forensics
   - Escalate to Security and Legal teams
```

---

## Generic Response Checklist

For any incident:

```
[ ] Acknowledge incident in PagerDuty/Slack
[ ] Designate incident commander
[ ] Open incident ticket
[ ] Notify stakeholders (team lead, on-call)
[ ] Begin diagnosis
[ ] Implement fix or mitigation
[ ] Verify fix worked
[ ] Document timeline
[ ] Close incident
[ ] Schedule post-mortem if severity >= 2
```

---

## Escalation Matrix

| Severity | Channel | Response Time | Examples |
|----------|---------|---------------|----------|
| P1 Critical | PagerDuty | 5 min | DB down, LLM error >20%, Audit broken |
| P2 High | PagerDuty | 15 min | Query latency >60s, Cache hit <20% |
| P3 Medium | Slack | 1 hour | LLM fallback >30%, DB slow |
| P4 Low | Slack | 4 hours | Cache optimization, minor latency |

---

## Useful Commands

```bash
# Health checks
curl -s http://localhost:8000/health/all | jq

# Logs
kubectl logs -n nrg -l app=nrg-api --tail=500 -f
kubectl logs -n nrg -l app=nrg-api --since=1h | grep ERROR

# Metrics
curl -s http://localhost:9090/metrics | grep nrg_

# Pod status
kubectl get pods -n nrg -o wide
kubectl top pods -n nrg

# Redis
redis-cli -h localhost -p 6379 info
redis-cli monitor | head -100

# Database
psql -h localhost -U nrg -d nrg_db -c "SELECT * FROM pg_stat_activity;"
```

---

## On-Call Rotation

Primary: ML Platform Team  
Secondary: Infrastructure Team  
Escalation: Engineering Manager

---

## Post-Incident Requirements

For P1/P2 incidents:
- Write detailed timeline
- Identify root cause
- Define action items with owners
- Schedule review in 1 week
- Update runbook if gap found

---

*Last updated: 2024-04-21*  
*Owner: ML Platform Team*  
*Review frequency: Monthly*