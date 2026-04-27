# NRG Data Protection Impact Assessment (DPIA) Template

> **Version:** 1.0  
> **Mandated by:** DPDP Act 2023, Section 8 (Significant Data Fiduciaries)  
> **Applicable to:** All high-risk processing activities at NRG  
> **Review cycle:** Before launch of new processing, and annually for existing processing  

---

## Section 1: DPIA Metadata

| Field | Value |
|-------|-------|
| **DPIA ID** | DPIA-NRG-YYYY-NNN |
| **Processing Activity** | [Name of activity] |
| **Department / Owner** | [Team name] |
| **DPO Review Date** | [Date] |
| **Next Review Date** | [Date + 12 months] |
| **Approval Status** | ☐ Draft  ☐ Under Review  ☐ Approved  ☐ Rejected |
| **Approving Authority** | [Name + Designation] |

---

## Section 2: Processing Description

### 2.1 Purpose

_What is the purpose of this processing activity? Why is it necessary?_

```
[Describe the business purpose, legal basis, and expected outcomes]
```

### 2.2 Personal Data Involved

| Data Category | Specific Elements | Volume (approx.) | Source |
|--------------|-------------------|-----------------|--------|
| Identifiers | | | |
| Contact Info | | | |
| Professional Data | | | |
| Behavioral Data | | | |
| Sensitive Personal Data | | | |

### 2.3 Data Subjects

| Category | Count | Vulnerability | Notes |
|----------|-------|--------------|-------|
| Researchers | | | |
| Students | | May include minors | |
| Government Officials | | | |
| General Public | | | |

### 2.4 Processing Operations

- [ ] Collection
- [ ] Recording
- [ ] Organization
- [ ] Structuring
- [ ] Storage
- [ ] Adaptation / Alteration
- [ ] Retrieval
- [ ] Consultation
- [ ] Use
- [ ] Disclosure by transmission
- [ ] Dissemination
- [ ] Alignment / Combination
- [ ] Restriction
- [ ] Erasure / Destruction

### 2.5 Retention Period

```
[Specify how long data will be retained and the justification]
```

---

## Section 3: Necessity & Proportionality Assessment

### 3.1 Necessity

_Is this processing necessary to achieve the stated purpose? Could the purpose be achieved with less data?_

| Question | Answer | Justification |
|----------|--------|---------------|
| Is all collected data strictly necessary? | ☐ Yes ☐ No | |
| Can the purpose be achieved with anonymized data? | ☐ Yes ☐ No | |
| Is the data minimization principle followed? | ☐ Yes ☐ No | |

### 3.2 Proportionality

_Is the processing proportionate to the purpose?_

| Question | Answer | Justification |
|----------|--------|---------------|
| Is the intrusion on privacy justified by the benefit? | ☐ Yes ☐ No | |
| Are less intrusive alternatives available? | ☐ Yes ☐ No | |
| Is the retention period no longer than necessary? | ☐ Yes ☐ No | |

---

## Section 4: Risk Assessment

### 4.1 Threat Identification

| Threat | Likelihood (1-5) | Impact (1-5) | Risk Score (L×I) | Existing Controls |
|--------|-----------------|-------------|-----------------|-------------------|
| Unauthorized access / breach | | | | |
| Data exfiltration (sovereignty violation) | | | | |
| Re-identification of anonymized data | | | | |
| Discrimination / profiling harm | | | | |
| Data quality issues leading to wrong decisions | | | | |
| Retention beyond legal period | | | | |
| Cross-border transfer violation | | | | |

### 4.2 Risk Scoring Matrix

| Score | Level | Action Required |
|-------|-------|-----------------|
| 1-4 | Low | Document and monitor |
| 5-9 | Medium | Mitigate within 30 days |
| 10-16 | High | Mitigate before processing begins |
| 17-25 | Critical | Processing cannot proceed |

### 4.3 Residual Risk

_After applying controls, what is the remaining risk?_

| Threat | Residual Likelihood | Residual Impact | Residual Score | Acceptable? |
|--------|-------------------|---------------|---------------|-------------|
| | | | | ☐ Yes ☐ No |

---

## Section 5: Mitigation Measures

### 5.1 Technical Measures

| Measure | Status | Owner | Target Date |
|---------|--------|-------|-------------|
| Encryption at rest (AES-256) | ☐ Implemented ☐ Planned | | |
| Encryption in transit (TLS 1.3) | ☐ Implemented ☐ Planned | | |
| Access controls (RBAC) | ☐ Implemented ☐ Planned | | |
| Pseudonymization | ☐ Implemented ☐ Planned | | |
| Audit logging (HMAC chain) | ☐ Implemented ☐ Planned | | |
| Data loss prevention (DLP) | ☐ Implemented ☐ Planned | | |
| Anomaly detection | ☐ Implemented ☐ Planned | | |

### 5.2 Organizational Measures

| Measure | Status | Owner | Target Date |
|---------|--------|-------|-------------|
| Staff training on DPDP | ☐ Implemented ☐ Planned | | |
| Data Processing Agreements | ☐ Implemented ☐ Planned | | |
| Incident response plan | ☐ Implemented ☐ Planned | | |
| Regular access reviews | ☐ Implemented ☐ Planned | | |
| Backup and recovery testing | ☐ Implemented ☐ Planned | | |

### 5.3 Consent & Transparency Measures

| Measure | Status | Owner | Target Date |
|---------|--------|-------|-------------|
| Privacy notice published | ☐ Implemented ☐ Planned | | |
| Granular consent obtained | ☐ Implemented ☐ Planned | | |
| Consent withdrawal mechanism | ☐ Implemented ☐ Planned | | |
| Data subject rights portal | ☐ Implemented ☐ Planned | | |

---

## Section 6: Stakeholder Consultation

| Stakeholder | Role | Consulted? | Feedback |
|------------|------|-----------|----------|
| Data Protection Officer | | ☐ Yes ☐ No | |
| IT Security Team | | ☐ Yes ☐ No | |
| Legal Counsel | | ☐ Yes ☐ No | |
| Data Subjects (sample) | | ☐ Yes ☐ No | |
| External Auditor | | ☐ Yes ☐ N/A | |

---

## Section 7: Compliance Mapping

### 7.1 DPDP Act 2023 Compliance

| Section | Requirement | Compliant? | Evidence |
|---------|-------------|-----------|----------|
| Section 4 | Lawful basis for processing | ☐ Yes ☐ No | |
| Section 6 | Consent requirements | ☐ Yes ☐ No | |
| Section 8 | Data fiduciary obligations | ☐ Yes ☐ No | |
| Section 12 | Right to access | ☐ Yes ☐ No | |
| Section 13 | Right to correction & erasure | ☐ Yes ☐ No | |
| Section 14 | Right to grievance redressal | ☐ Yes ☐ No | |
| Section 15 | Data protection officer | ☐ Yes ☐ No | |
| Section 16 | Independent data auditor | ☐ Yes ☐ No | |

### 7.2 CERT-In Compliance

| Requirement | Compliant? | Evidence |
|-------------|-----------|----------|
| Incident reporting (6-hour) | ☐ Yes ☐ No | |
| Data localization | ☐ Yes ☐ No | |
| Log retention (180 days) | ☐ Yes ☐ No | |

---

## Section 8: Approval

### 8.1 DPO Assessment

```
[DPO to complete after review]

The proposed processing activity has been reviewed against the DPDP Act 2023
and associated guidelines. Based on the risk assessment and mitigation measures
identified, I conclude that:

☐ The processing may proceed as proposed
☐ The processing may proceed with conditions (specify below)
☐ The processing cannot proceed (specify reasons below)

Conditions / Reasons:
_______________________________________________________________
_______________________________________________________________

DPO Signature: _________________________ Date: _______________
```

### 8.2 Final Approval

```
[Approving Authority — Director, IIT-GN or designated authority]

I approve this DPIA and authorize the processing activity described herein,
subject to the conditions and mitigation measures identified.

☐ Approved
☐ Approved with modifications
☐ Rejected

Modifications (if any):
_______________________________________________________________
_______________________________________________________________

Signature: _________________________ Date: _______________
Name: _____________________________
Designation: _______________________
```

---

## Section 9: Review Log

| Date | Reviewer | Changes | Action |
|------|----------|---------|--------|
| | | | |
| | | | |

---

## Appendix A: Example — NRG Query Processing DPIA

### A.1 Processing Activity
**Natural language query processing with text-to-SQL and RAG**

### A.2 Personal Data
- Query text (may contain personal references)
- Session ID linked to user account
- Tier classification (public/industry/academic/government)

### A.3 Risk Assessment
| Threat | L | I | Score | Mitigation |
|--------|---|---|-------|------------|
| Query logs reveal research interests | 4 | 3 | 12 | Anonymize after 90 days; audit access |
| SQL injection via query | 3 | 5 | 15 | Parameterized queries; adversarial testing |
| Tier escalation | 2 | 4 | 8 | RBAC enforcement; anomaly detection |

### A.4 DPO Conclusion
**Approved with conditions:** Query logs anonymized within 90 days; adversarial testing (LB-2) passes before production.

---

*Template based on DPDP Act 2023 and MeitY guidelines for Significant Data Fiduciaries.*
