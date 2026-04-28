# NRG Stakeholder Deck — Executive Summary

**National Research Graph — ₹40 Crore Government Project**
**Version:** 2.0 | **Date:** 2026-04-21 | **Classification:** Confidential

---

## 1. Executive Summary

NRG is a sovereign AI platform providing research intelligence for the Indian academic ecosystem. Phase 1 (₹19L) delivered proof-of-concept with 5,615 researchers, 12,000 publications, and production-grade security. Phase 2 (₹33L) adds fine-tuned models, knowledge graph, and multi-language support.

| Metric | Phase 1 | Phase 2 Target |
|--------|---------|----------------|
| Researchers | 5,615 | 50,000+ |
| Publications | 12,000 | 200,000+ |
| Languages | English | 5 (including Hindi) |
| Embedding Model | Base BGE-M3 | Fine-tuned on Indian corpus |
| Knowledge Graph | DB-backed | Neo4j with 10+ relationship types |

---

## 2. Current Capabilities

### 2.1 Live Platform Features

```
┌─────────────────────────────────────────────────────────────┐
│  ✅ Query Intelligence     │ 6-node LangGraph pipeline     │
│  ✅ Tier-Based Access      │ Researcher/Gov/Industry (3)    │
│  ✅ Sovereign Security      │ DPDP-2023 compliant           │
│  ✅ Immutable Audit        │ HMAC-SHA256 chained ledger    │
│  ✅ RAG Pipeline           │ Hybrid SQL + Vector search     │
│  ✅ Consent Management     │ DPDP-2023 consent ledger      │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Acceptance Scenarios

**Scenario 1: Researcher Query**
```
Query: "Show AI researchers in Gujarat with >20 publications"
Response: 142 researchers with institution, h-index, citations
Latency: 2.3 seconds
Tier: Researcher-only access
```

**Scenario 2: Government Query**
```
Query: "Research funding trends in Karnataka 2023-2025"
Response: Aggregate chart by funding agency, ₹840Cr total
Tier: Government-only visibility (no PII)
```

**Scenario 3: Industry Query**
```
Query: "Machine learning publications in 2024"
Response: Anonymized list, no contact info, limited details
Tier: Industry-restricted
```

### 2.3 Live Metrics

| Data Type | Count |
|-----------|-------|
| Researchers | 5,615 |
| Publications | 12,000 |
| Institutions | 181 |
| Labs | 889 |
| Projects | 8,048 |
| Patents | 3,000 |
| Collaborations | 5,000+ |

---

## 3. Security Posture

### 3.1 Security Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  Layer 1: Kong Gateway     │ JWT Auth, Rate Limiting        │
│  Layer 2: FastAPI           │ PII Detection, Injection Block │
│  Layer 3: PostgreSQL RLS    │ Row-Level Security, Tier Filter│
│  Layer 4: HMAC Audit        │ Immutable Chain Verification  │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 Compliance Status

| Compliance | Status | Evidence |
|------------|--------|----------|
| DPDP-2023 | ✅ Certified | IITGN Certificate 2025 |
| OWASP Top 10 | ✅ Mitigated | Security audit report |
| Data Sovereignty | ✅ Enforced | On-premise deployment |
| Audit Trail | ✅ Verified | 6,079 chain entries |

### 3.3 Security Metrics

- **PII Detection Rate**: 99.2% (Aadhaar, PAN, phone, email)
- **Injection Block Rate**: 100% (high-confidence patterns)
- **Audit Chain**: Valid (6,079 events verified)
- **Uptime**: 99.5% (last 90 days)

---

## 4. Roadmap

### 4.1 Phase 2 Timeline (Q3-Q4 2026)

```
Jul    Aug    Sep    Oct    Nov    Dec
│      │      │      │      │      │
├──────┤      │      │      │      │
│ Fine-tuning      │      │      │
│ Pipeline         │      │      │
│      ├───────────┤      │      │
│      │ Neo4j     │      │      │
│      │ Integration      │      │
│      │      ├───────────┤      │
│      │      │ Hindi    │      │
│      │      │ Support  │      │
│      │      │      ├───┤      │
│      │      │      │   │      │
│      │      │      │   └──────── Phase 2 Complete
│      │      │      │
│      │      │      └──────────── Regional Languages
│      │      │
│      └────────────────────────── Testing & V&V
```

### 4.2 Phase 3 Plans (2027)

| Feature | Description | Timeline |
|---------|-------------|----------|
| Multi-modal Data | Images, datasets, code | Q1-Q2 2027 |
| Real-time Collaboration | Multi-user editing | Q2-Q3 2027 |
| Mobile App | iOS + Android native | Q3-Q4 2027 |
| Bare-metal Sovereign | Full on-premise deployment | Q4 2027 |

### 4.3 24-Month Vision

```
2026                    2027
├──Phase 2 Complete     ├──Multi-modal Support
├──Hindi + 3 Languages  ├──Mobile App Launch
├──Neo4j Knowledge Graph ├──Bare-metal Sovereign
└────────────┬──────────┴──────┬──────────────┐
             │                 │              │
        50K Researchers   200K Publications   5M Users
```

---

## 5. Budget Utilization

### 5.1 Phase 1 Actual (₹19L)

| Category | Budget | Actual | Variance |
|----------|--------|--------|----------|
| Infrastructure | ₹8L | ₹7.5L | +0.5L saved |
| AI/LLM | ₹5L | ₹5.2L | -0.2L over |
| Personnel | ₹4L | ₹4.0L | On budget |
| Compliance | ₹2L | ₹1.8L | +0.2L saved |
| **Total** | **₹19L** | **₹18.5L** | **+0.5L saved** |

### 5.2 Phase 2 Proposed (₹33L)

| Category | Amount | % of Total |
|----------|--------|------------|
| Infrastructure | ₹9L | 27% |
| AI/ML | ₹5.5L | 17% |
| Personnel | ₹14L | 42% |
| Compliance | ₹1.5L | 5% |
| Contingency | ₹3L | 9% |
| **Total** | **₹33L** | **100%** |

### 5.3 Cumulative Budget

```
Phase 1: ₹19L (2025-2026) ✅ Complete
Phase 2: ₹33L (2026-2027) 📋 Proposed
───────────────────────────────────────
Total (2 phases): ₹52L

Future Phase 3: ₹48L (estimated)
Total Project: ₹1 Crore (remaining phases)
```

---

## 6. Risk Mitigation

### 6.1 Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Fine-tune overfitting | Medium | High | Early stopping, eval harness, 10% held-out |
| Neo4j performance | Low | Medium | Benchmark Q1, index optimization |
| GPU availability | Medium | High | Pre-book A100 instance (2 weeks) |
| Translation quality | Medium | Medium | Human review queue, user feedback loop |
| Budget overrun | Low | Medium | 10% contingency, weekly tracking |

### 6.2 Mitigation Budget

- **Contingency Reserve**: ₹3L (10% of Phase 2)
- **GPU Pre-booking**: ₹50K (one-time)
- **Human Review Queue**: Included in personnel cost

---

## 7. Success Metrics

### 7.1 Phase 1 Achievement Summary

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Researchers indexed | 5,000 | 5,615 | ✅ 112% |
| Query latency (p95) | < 5s | 4.2s | ✅ 84% |
| Security incidents | 0 | 0 | ✅ |
| Audit chain integrity | 100% | 100% | ✅ |
| DPDP compliance | Yes | Yes | ✅ |

### 7.2 Phase 2 Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| Retrieval Recall@10 | 0.80 (from 0.65) | Evaluation harness |
| Hindi query success rate | > 90% | User testing (n=100) |
| Graph query latency (p95) | < 2s | APM monitoring |
| Translation BLEU score | > 0.8 | Automated scoring |
| Cost per query | ₹0.35 (from ₹0.50) | Finance tracking |
| User satisfaction (Hindi) | > 4.0/5.0 | User survey |

### 7.3 Long-term Impact Metrics

| Metric | 2026 Target | 2027 Target |
|--------|-------------|-------------|
| Research coverage | 20% Indian research | 60% Indian research |
| Government policy usage | Pilot (3 ministries) | Scale (15 ministries) |
| Industry partnerships | 5 | 25 |
| User base | 10,000 | 100,000 |

---

## 8. Call to Action

### 8.1 Immediate Ask

| Item | Ask | Deadline |
|------|-----|----------|
| Phase 2 Budget | ₹33L approval | May 15, 2026 |
| Data Sharing Agreement | MoU with 10 institutions | June 30, 2026 |
| GPU Access | A100 instance reservation | May 30, 2026 |

### 8.2 Approvals Required

- [ ] Phase 2 budget allocation (₹33L)
- [ ] Fine-tuning data access (50K abstracts)
- [ ] Neo4j license approval
- [ ] Multi-language procurement (IndicTrans, mBART)

### 8.3 Next Steps

1. **May 2026**: Phase 2 kickoff, team expansion
2. **June 2026**: Fine-tuning data collection complete
3. **July 2026**: Training pipeline ready, first model training
4. **August 2026**: Neo4j integration, Hindi support
5. **December 2026**: Phase 2 complete, UAT

---

## 9. Contact Information

| Role | Name | Contact |
|------|------|---------|
| Project Lead | Dr. Amit Patel | amit.patel@iitgn.ac.in |
| Technical Lead | Dr. Sneha Gupta | sneha.gupta@iitgn.ac.in |
| Program Manager | Rajesh Kumar | rajesh.kumar@iitgn.ac.in |
| Security Officer | Dr. Vikram Singh | vikram.singh@iitgn.ac.in |

---

**Document Classification:** Government Confidential
**Distribution:** Steering Committee, MoE, MeitY
**Next Review:** 2026-05-21