# NRG Privacy Notice

> **Version:** 1.0  
> **Effective Date:** [TBD — upon DPDP Board registration]  
> **Last Updated:** 2026-04-25  
> **Data Fiduciary:** National Research Graph (NRG), IIT Gandhinagar  
> **DPO:** [TBD — will be appointed before SDF registration]  
> **Grievance Officer:** grievance@nrg.gov.in  

---

## 1. Introduction

The National Research Graph (NRG) is India's sovereign research database, operated by IIT Gandhinagar under the National Informatics Centre (NIC) and Ministry of Electronics and Information Technology (MeitY).

This Privacy Notice explains how we collect, use, store, and protect your personal data when you use the NRG platform. It is issued in compliance with the **Digital Personal Data Protection Act, 2023** (DPDP Act).

---

## 2. What Data We Collect

### 2.1 Researcher Data

| Data Element | Purpose | Legal Basis |
|-------------|---------|-------------|
| Name | Profile display, search indexing | Consent |
| Institutional email | Authentication, communication | Consent |
| ORCID iD | Deduplication, cross-platform linkage | Consent |
| Research publications | Academic visibility, citation analysis | Legitimate use (employment) |
| h-index / citations | Research impact metrics | Legitimate use (employment) |
| Department / lab affiliation | Institutional analytics | Consent |

### 2.2 User Account Data

| Data Element | Purpose | Legal Basis |
|-------------|---------|-------------|
| Username | Platform authentication | Consent |
| Password (hashed) | Authentication | Consent |
| Tier assignment (public/industry/academic/government) | Access control | Contract / government function |
| Session logs | Security, audit compliance | Legal obligation |
| IP address (hashed) | Fraud detection, rate limiting | Legitimate use |

### 2.3 Query Data

| Data Element | Purpose | Legal Basis |
|-------------|---------|-------------|
| Search queries | Improving search relevance | Consent (anonymized) |
| Query timestamp | Usage analytics | Legitimate use |
| Query results accessed | Personalization | Consent |

### 2.4 We Do NOT Collect

- Aadhaar numbers
- PAN card numbers
- Phone numbers
- Biometric data
- Financial account details
- Location data (beyond institutional affiliation)

---

## 3. How We Use Your Data

### 3.1 Primary Purposes

1. **Research Discovery:** Enable search and discovery of Indian research output
2. **Collaboration Matching:** Suggest potential collaborators based on research interests
3. **Policy Analytics:** Provide aggregate insights to government agencies (no individual PII)
4. **Platform Security:** Prevent abuse, detect anomalies, enforce tier-based access

### 3.2 Secondary Purposes (with separate consent)

- Inclusion in public researcher directories
- Contact by verified government agencies for policy consultation
- Inclusion in aggregate statistics and trend reports
- Email notifications about platform updates

---

## 4. Data Sharing

### 4.1 Within NRG (Internal)

Your data is shared across NRG subsystems (API, search, analytics) only as necessary to fulfill the purposes above. All access is logged to the immutable audit chain.

### 4.2 With Third Parties

| Recipient | Data Shared | Purpose | Safeguards |
|-----------|------------|---------|------------|
| Government agencies (government tier) | Aggregate statistics only | Policy formulation | DPDP Section 7 exemption |
| IIT-GN IT services | System logs | Infrastructure maintenance | Data Processing Agreement |
| NIC / MeitY | Compliance reports | Regulatory oversight | Government function exemption |

**We never sell your data. We never share PII with commercial entities.**

### 4.3 Cross-Border Transfer

NRG is a **sovereign platform**. Your data never leaves Indian territory. No cross-border transfers occur.

---

## 5. Data Retention

| Data Category | Retention Period | Deletion Trigger |
|---------------|-----------------|------------------|
| Active user profile | Duration of account | Account deletion request |
| Research publications | Indefinite | Withdrawal by publisher |
| Query logs (raw) | 90 days | Automatic purge |
| Query logs (anonymized) | 7 years | Institutional policy |
| Audit logs | 7 years | Legal requirement |
| Session tokens | 24 hours | Expiry |
| Backup copies | 90 days | Rotation schedule |

---

## 6. Your Rights (DPDP Act)

As a Data Principal, you have the following rights:

### 6.1 Right to Access
Request a copy of all personal data we hold about you.
- **How:** Email dpo@nrg.gov.in with subject "Data Access Request"
- **Response time:** 30 days
- **Format:** JSON export via secure download link

### 6.2 Right to Correction
Request correction of inaccurate or incomplete data.
- **How:** Use "Edit Profile" in the NRG dashboard, or email dpo@nrg.gov.in
- **Response time:** 15 days

### 6.3 Right to Erasure (Deletion)
Request deletion of your personal data.
- **How:** Email dpo@nrg.gov.in with subject "Data Deletion Request"
- **Limitations:** We may retain anonymized research metadata and audit logs as required by law
- **Response time:** 30 days

### 6.4 Right to Grievance Redressal
File a complaint if you believe your data rights have been violated.
- **How:** Email grievance@nrg.gov.in
- **Escalation:** Data Protection Board of India if unresolved within 30 days

### 6.5 Right to Nominate
Nominate a representative to exercise your rights in case of incapacity.
- **How:** Submit nomination form via NRG dashboard

---

## 7. Security Measures

| Measure | Implementation |
|---------|---------------|
| Encryption at rest | AES-256 for all databases and backups |
| Encryption in transit | TLS 1.3 for all communications |
| Access control | RBAC with tier-based permissions |
| Audit logging | Immutable HMAC-signed audit chain |
| Pseudonymization | Internal IDs mapped to external identifiers |
| Backup encryption | GPG-encrypted backups on Indian-soil storage |
| Incident response | 72-hour breach notification to DPB + affected principals |

---

## 8. Consent Mechanism

### 8.1 Registration Consent

During registration, you will be asked for **granular consent** for specific purposes:

```
☐ I consent to my profile being visible to other researchers on NRG
☐ I consent to my data being included in aggregate institutional statistics
☐ I consent to being contacted by verified government agencies for policy purposes
☐ I consent to receiving platform updates and newsletters
```

Each checkbox is **independent**. You may withdraw any consent at any time without affecting other services.

### 8.2 Consent Withdrawal

- **How:** Visit "My Consents" in the NRG dashboard, or email dpo@nrg.gov.in
- **Effect:** Withdrawal is effective within 24 hours
- **Consequence:** Only affects future processing; previously published data may remain in anonymized form

---

## 9. Children's Data

NRG is intended for researchers and professionals. If you are under 18, **verifiable parental consent** is required before account creation. Contact dpo@nrg.gov.in for the parental consent process.

---

## 10. Updates to This Notice

We may update this Privacy Notice to reflect changes in law or platform features. You will be notified via:
- Email to your registered address
- Banner notification on the NRG platform
- Update log in the "Legal" section of your dashboard

**Significant changes require renewed consent.**

---

## 11. Contact

| Role | Contact | Response Time |
|------|---------|--------------|
| Data Protection Officer | dpo@nrg.gov.in | 2 business days |
| Grievance Officer | grievance@nrg.gov.in | 5 business days |
| General queries | support@nrg.gov.in | 1 business day |
| Security incidents | security@nrg.gov.in | Immediate (24/7) |

---

## 12. Legal Basis Summary

| Processing Activity | DPDP Basis | Section |
|--------------------|-----------|---------|
| Profile creation | Consent | Section 6 |
| Aggregate analytics | Legitimate use | Section 7 |
| Government access | Government function | Section 7(2) |
| Security logging | Legal obligation | Section 7(2) |
| Researcher directory | Consent | Section 6 |

---

*This Privacy Notice is issued under the authority of IIT Gandhinagar as the Data Fiduciary for NRG. It complies with the Digital Personal Data Protection Act, 2023 and associated rules.*
