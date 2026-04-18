# NRG DPDP 2023 Compliance Mapping v1.0

## Clause-to-Implementation Matrix

| Clause | Requirement | Implementation | Evidence Artifact |
|--------|-------------|-----------------|-------------------|
| Clause 5 | Purpose limitation | RBAC tier system | docs/architecture/RBAC_POLICY.md |
| Clause 6 | Notice | Privacy notice UI | src/api/routes/privacy.py |
| Clause 7 | Consent | MFA + consent checkbox | src/auth/middleware.py |
| Clause 8 | Data fiduciary | Role: Data Steward | docs/ops/ROLES.md |
| Clause 9 | Legal basis | Contract + employment | Legal docs |
| Clause 10 | Medical research | Exemption handler | src/security/exemptions.py |
| Clause 11 | Government security | Exemption doc | docs/compliance/government_exemption.md |
| Clause 12 | SDF registration | IIT as SDF | docs/compliance/sdf_registration.md |

## Data Subject Rights (DSR) Workflow

### Right to Access
```
GET /dsr/access
→ Verify identity (MFA)
→ Fetch user data (Postgres)
→ Return JSON
```

### Right to Correction
```
PUT /dsr/correct
→ Verify identity (MFA)
→ Validate correction
→ Update Postgres
→ Log audit
```

### Right to Deletion
```
DELETE /dsr/delete
→ Verify identity (MFA)
→ Anonymize (NOT delete) - legal hold
→ Update audit_log
```

### Right to Portability
```
GET /dsr/export
→ Verify identity (MFA)
→ Create JSON export
→ Secure download link
```

## Consent Log

```sql
CREATE TABLE consent_log (
    consent_id UUID PRIMARY KEY,
    user_id UUID,
    consent_type VARCHAR(50),
    granted BOOLEAN,
    timestamp TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent VARCHAR(255)
);
```

## Grievance Officer

| Role | Name | Contact |
|------|------|---------|
| Grievance Officer | [TBD] | grievance@nrg.org.in |
| DPO | [TBD] | dpo@nrg.org.in |

## Retention Schedule

| Data Category | Retention Period | Basis |
|---------------|------------------|-------|
| Query logs | 7 years | Legal hold |
| Audit logs | 7 years | Compliance |
| User profiles | Active + 3 years | Operational |
| Research data | Indefinite | Institutional |

---

*External lawyer can sign off on this mapping.*