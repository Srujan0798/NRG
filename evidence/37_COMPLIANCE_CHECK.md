# Compliance Check Evidence — NRG

**Skill**: compliance-check
**Applied**: Sat Apr 25 2026
**Evidence File**: `evidence/37_COMPLIANCE_CHECK.md`

---

## Compliance Check: NRG Platform

### Summary

**Assessment**: Proceed with conditions

NRG is a research data platform that processes Indian academic data. Key compliance areas: **DPDP-2023** (India's data protection law), **GDPR** (if EU researchers are involved), and general security standards.

---

## Applicable Regulations

| Regulation | Jurisdiction | Relevance to NRG |
|-----------|--------------|-----------------|
| DPDP-2023 | India | Primary — platform processes Indian researcher data |
| GDPR | EU/EEA | Secondary — if EU researchers access platform |
| SOC 2 | Global | Security — enterprise customers may require |
| ISO 27001 | Global | Security — information security standard |

---

## DPDP-2023 Compliance (India)

### Key Requirements

| Requirement | NRG Status | Action Needed |
|-------------|-----------|---------------|
| Consent for data processing | ✅ Implemented | DPDPConsentDialog exists |
| Purpose limitation | ✅ Implemented | `dataPurpose` field in consent |
| Data minimization | ⚠️ Partial | SQL injection at line 479 bypasses validation |
| Security measures | ⚠️ Issues | See security-audit findings |
| Data principal rights | ✅ Implemented | DPDPAuditLog, DPDPWithdrawalPanel |
| Breach notification | ❌ Unknown | No breach notification flow found |

---

## GDPR Compliance (EU Researchers)

### Key Requirements

| Requirement | NRG Status | Action Needed |
|-------------|-----------|---------------|
| Lawful basis (consent/contract) | ✅ Implemented | Consent dialog + legitimate interest |
| Data subject access requests | ✅ Implemented | DPDPAuditLog shows user data |
| Right to erasure | ✅ Implemented | DPDPWithdrawalPanel |
| Data portability | ⚠️ Partial | No export function found |
| International transfers | ⚠️ Unknown | May involve cross-border data |
| DPIA (if high risk) | ❌ Not done | Required if processing special categories |

**Note**: NRG appears to target primarily Indian institutions. GDPR applicability depends on whether EU researchers access the platform.

---

## SOC 2 Compliance

### Relevance

Enterprise/government customers (Tier 2/3) may require SOC 2 compliance.

### Key Controls Missing

| Control | NRG Status |
|---------|-----------|
| Access management | ✅ Implemented | JWT auth, role-based |
| Encryption in transit | ✅ Implemented | HTTPS |
| Encryption at rest | ❌ Unknown | No evidence of DB encryption |
| Audit logging | ✅ Implemented | Audit chain exists |
| Incident response | ⚠️ Partial | No documented IRP found |
| Vulnerability management | ⚠️ Issues | SQL injection, Qdrant down |

---

## Data Processing Agreement (DPA)

### NRG as Data Processor

If NRG processes data on behalf of government/academic institutions:

| Element | Status |
|---------|--------|
| Written contract | ❌ No DPA found |
| Processing scope defined | ✅ Research data analysis |
| Security measures | ⚠️ Issues (SQL injection) |
| Sub-processor controls | ❌ No sub-processor list found |
| Breach notification (72h) | ❌ No IRP found |

---

## Risk Areas

| Risk | Severity | Mitigation |
|------|----------|------------|
| SQL injection leaks researcher data | 🔴 Critical | Fix line 479 immediately |
| DPDP consent not obtained | 🟡 Medium | Consent dialog exists — verify it's shown |
| No breach notification IRP | 🟡 Medium | Create incident response plan |
| DB encryption at rest missing | 🟡 Medium | Add encryption for production |
| Cross-border transfer (GDPR) | 🟡 Medium | Verify data stays in India |
| No DPIA for special categories | 🟡 Medium | Conduct DPIA if processing biometrics/health |

---

## Required Actions

### Immediate (Before Next Deploy)

1. **Fix SQL injection** — Line 479 CRITICAL
2. **Rotate JWT secrets** — Default in source is BLOCKING

### Short-Term (This Sprint)

3. **Create breach notification IRP** — DPDP requires 72h notification
4. **Add DB encryption at rest** — Use PostgreSQL encryption
5. **Document sub-processors** — List all third-party services

### Medium-Term (Next Quarter)

6. **Conduct DPIA** — If processing special category data
7. **Assess GDPR applicability** — If EU researchers are users
8. **SOC 2 readiness** — If targeting enterprise customers

---

## Approvals Needed

| Approver | Why | Status |
|----------|-----|--------|
| Legal | DPDP compliance sign-off | Pending |
| Security | SQL injection fix verification | Pending |
| CTO | Production encryption decision | Pending |

---

## Further Review Recommended

1. **Privacy Impact Assessment** — Conduct formal DPIA for government tier data flows
2. **Cross-border data flow analysis** — Verify data localization for government data
3. **Vendor security review** — Assess third-party services (Qdrant, Anthropic)

---

## Skill Deliverable

**Status**: COMPLETED

Compliance check found:
- DPDP-2023: Consent mechanism exists, but SQL injection threatens data
- GDPR: Secondary (depends on EU researcher involvement)
- SOC 2: Missing IRP, DB encryption, vulnerability management
- Critical: Fix SQL injection before next deploy
- Required: Create breach notification IRP
