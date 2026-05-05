---
name: nrg-dpdp-compliance
description: Use when designing or auditing NRG consent, data-subject rights, localization, privacy notices, DPIA work, or DPDP Act 2023 compliance.
---

# NRG DPDP Compliance Skill

India's Digital Personal Data Protection (DPDP) Act 2023 compliance for the National Research Graph (NRG).

## When to Use

Use this skill when:
- Designing consent flows for NRG data subjects
- Auditing data processing activities for DPDP compliance
- Reviewing data localization requirements
- Preparing for CERT-In or government audits
- Implementing data subject rights (access, correction, erasure)
- Writing privacy notices or DPIA (Data Protection Impact Assessment)

## DPDP Act 2023: Key Obligations

### 1. Lawful Basis for Processing (Section 4)

NRG must have valid grounds:

| Basis | NRG Application | Example |
|-------|----------------|---------|
| **Consent** | Primary basis for non-government users | Researcher opts in to profile creation |
| **Legitimate Uses** | Government function, employment, legal obligation | Government tier accessing research data for policy |
| **Certain Other Purposes** | Deemed consent for existing relationships | IIT-GN researchers already in system |

**Verifiable parental consent** required for data principals <18 years.

### 2. Consent Requirements (Section 6)

Consent must be:
- **Free** — no coercion or condition of service
- **Specific** — separate consent for each purpose
- **Informed** — clear notice in English + 22 scheduled languages
- **Unconditional** — withdrawable anytime without detriment
- **Verifiable** — auditable log of consent grant/withdrawal

### 3. NRG Consent Flow Design

```
User Registration
      ↓
Privacy Notice (Layered)
  ├─ Layer 1: Summary (1 page, 22 languages)
  ├─ Layer 2: Purpose-specific consents
  └─ Layer 3: Full policy
      ↓
Granular Consent Checkboxes
  ☐ Profile visibility to other researchers
  ☐ Inclusion in aggregate statistics
  ☐ Contact by government agencies (policy purposes)
  ☐ Publication metadata indexing
      ↓
Consent Record → Audit Chain (HMAC + timestamp)
      ↓
Dashboard → "My Consents" → Withdraw anytime
```

### 4. Data Fiduciary Obligations (Section 8)

NRG as Data Fiduciary must:

- [ ] Implement **reasonable security safeguards** (encryption at rest + in transit)
- [ ] **Notify Data Protection Board** + affected principals of personal data breaches within 72 hours
- [ ] **Erase** personal data when purpose fulfilled or consent withdrawn
- [ ] **Appoint Data Protection Officer** (DPO) — mandatory for Significant Data Fiduciaries
- [ ] **Appoint Independent Data Auditor** — mandatory for SDFs
- [ ] **Conduct DPIA** before high-risk processing

### 5. Data Principal Rights (Sections 12-14)

| Right | NRG Implementation | API Endpoint |
|-------|-------------------|--------------|
| **Access** | View all personal data held | `GET /api/v1/me/data` |
| **Correction** | Update inaccurate data | `PUT /api/v1/me/data` |
| **Erasure** | Delete personal data | `DELETE /api/v1/me/data` |
| **Grievance Redressal** | File complaint via DPO | `POST /api/v1/grievance` |
| **Nomination** | Nominate representative | `POST /api/v1/me/nominee` |

**Government override:** Government can exempt agencies from certain provisions via notification (Section 17). NRG must track which datasets fall under exemption.

### 6. Data Localization

DPDP Act does NOT mandate storage within India. However, NRG's **sovereign mandate** requires:

- All personal data stored on Indian soil
- No cross-border transfer without Data Protection Board approval
- Backup copies within Indian territory only
- Cloud providers must have Indian data centers with contractual data residency clauses

### 7. Significant Data Fiduciary (SDF) Criteria

NRG likely qualifies as SDF because:
- Processes data of 50k+ researchers (volume)
- Government-linked (sensitive nature)
- Uses AI/ML for profiling (risk of harm)
- High risk to rights of data principals

**SDF obligations:**
- DPO appointment (resident in India)
- Independent data auditor
- Periodic DPIA
- Additional security measures as prescribed

## NRG DPDP Compliance Checklist

### Technical Controls

- [ ] **Encryption at rest:** AES-256 for database, Qdrant vectors, backups
- [ ] **Encryption in transit:** TLS 1.2+ for all communications
- [ ] **Pseudonymization:** Researcher IDs mapped internally; external identifiers hashed
- [ ] **Access logging:** Every personal data access logged to audit chain
- [ ] **Consent management system:** Granular, verifiable, auditable
- [ ] **Data retention scheduler:** Auto-delete after retention period
- [ ] **Breach detection:** Automated alerts for anomalous access patterns
- [ ] **Right to erasure:** Hard delete + cascade to Qdrant vectors

### Organizational Controls

- [ ] **DPO appointed:** Name, contact, reporting line documented
- [ ] **Privacy policy:** Published in English + 22 scheduled languages
- [ ] **Consent records:** Stored immutably in audit chain
- [ ] **Data processing register:** Inventory of all personal data processing
- [ ] **Vendor agreements:** DPA clauses with all subprocessors
- [ ] **Training:** Annual DPDP training for all staff
- [ ] **Incident response plan:** 72-hour breach notification procedure

### Audit Artifacts

| Artifact | Location | Review Frequency |
|----------|----------|-----------------|
| DPIA | `docs/compliance/dpia/` | Before new high-risk processing |
| Consent logs | Audit chain (`nrg_audit_events`) | Continuous |
| Access reviews | `docs/compliance/access_reviews/` | Quarterly |
| Vendor DPAs | `docs/compliance/dpas/` | Annual |
| Breach register | `docs/compliance/breach_register/` | Per incident |

## DPDP + NRG Tier System

| Tier | Personal Data Access | Consent Requirement | Special Notes |
|------|---------------------|---------------------|---------------|
| **Public** | None (aggregate only) | None for aggregate | No PII exposure |
| **Industry** | Company-level aggregate | Consent for profile | No individual researcher PII |
| **Academic** | Own + department aggregate | Consent for public profile | Can opt out of statistics |
| **Government** | Full (policy mandate) | Deemed consent (Section 7) | Exempt from certain provisions |

## Penalties (Section 33)

| Violation | Penalty |
|-----------|---------|
| Breach of reasonable security | Up to ₹250 crore |
| Failure to notify breach | Up to ₹200 crore |
| Non-compliance with Board directions | Up to ₹50 crore |
| Violation of processing provisions | Up to ₹150 crore |

## Sovereign Note

NRG's sovereign mandate amplifies DPDP requirements:
- Data must never leave Indian jurisdiction
- Government access must be logged with higher granularity
- Audit chain serves as immutable consent + access record
- CERT-In reporting in addition to Data Protection Board
