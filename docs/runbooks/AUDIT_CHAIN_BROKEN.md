# Runbook: Audit Chain Broken

## Alert
`nrg_audit_chain_integrity == 0`

## Severity
CRITICAL

## Symptoms
- `/audit/verify` returns `ok: false`
- Chain file has been tampered with
- HMAC verification fails at specific line

## Verification

```bash
# Check chain status
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  http://localhost:8000/audit/verify

# Inspect chain file
python -c "from src.audit import verify_chain; print(verify_chain())"

# Check recent chain entries
tail -50 .audit/chain.jsonl
```

## Mitigation

### If tampering detected:

1. **STOP** all write operations to audit chain
2. **QUARANTINE** the affected segment
3. **NOTIFY** security team immediately
4. **INVESTIGATE** access logs for unauthorized access

### Chain recovery:

```bash
# Seal chain at last known good point
python -c "from src.audit import get_audit_log; get_audit_log().seal_segment('breach_detected')"

# Archive compromised segment
cp .audit/chain.jsonl .audit/chain.jsonl.compromised.$(date +%s)

# Restore from backup (if available)
# Chain must be re-verified after restoration
```

## Rollback

1. Restore from nightly backup (if verified clean)
2. Re-initialize chain with new key
3. Full security audit required before resuming operations

## Owner
Security Team (security@nrg.india)

## Post-Incident Actions

1. Root cause analysis
2. Key rotation
3. Access control review
4. Incident report within 24 hours

## Related Dashboards
- Audit Chain Integrity: http://grafana/d/audit-chain
- Security Events: http://grafana/d/security-events
