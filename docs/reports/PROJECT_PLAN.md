# National Research Intelligence Platform - Project Plan

## PROJECT OVERVIEW
- **Name**: National Research Intelligence Platform (India)
- **Dataset**: 600GB confidential research database
- **Budget**: ~40 crore INR (Gujarat government)
- **Execution**: IIT Gandhinagar
- **Core Security**: Zero-data-leakage architecture

---

## TECHNICAL ARCHITECTURE

### Core Principle
- Data NEVER leaves controlled infrastructure
- External LLMs (Gemini/Claude) used ONLY for reasoning, not storage
- 100% verifiable & auditable outputs

### Architecture Layers

1. **Data Storage Layer**
   - PostgreSQL (structured metadata)
   - Qdrant (vector embeddings for unstructured text)
   - Local deployment only
   - 600GB dataset

2. **Orchestration Layer**
   - LangGraph (agentic control flow)
   - Skill-based routing
   - State management

3. **Tool Skills**
   - Text-to-SQL generator
   - Local RAG (vector search)
   - Both execute LOCALLY

4. **Cloud Reasoning**
   - Gemini/Claude APIs
   - Receive ONLY retrieved facts (no raw data)
   - Return execution plans only

5. **Interface Layer**
   - Web UI (Streamlit → React)
   - Role-based access (3 tiers)
   - Structured output display

---

## USER PERSONAS & ACCESS

### Tier 1: Researchers
- Access: Granular details, contact info, collaboration data
- Output: Profiles, documents, specifics

### Tier 2: Government/Policymakers
- Access: High-level trends, institutional summaries, funding data
- Output: Reports, comparisons, analytics

### Tier 3: Industry
- Access: Capability mapping, partnership opportunities
- Output: Technical specs, contact info, strategic insights

---

## IMPLEMENTATION ROADMAP

### Phase 1: PoC - Validate Core [Months 1-2]

**Goals:**
- Prove zero-leakage architecture
- Demonstrate end-to-end flow
- Validate technical stack

**Deliverables:**
- LangGraph orchestration setup
- PostgreSQL + Qdrant Docker containers
- Text-to-SQL skill (read-only execution)
- RAG skill (local embedding model)
- 1GB synthetic dataset for testing
- Basic API gateway
- Immutable audit logging (Langfuse)

**Success Criteria:**
- Agent can interpret complex queries
- Routes correctly to appropriate database
- Synthesis happens on retrieved data only
- Complete audit trail generated
- Zero raw data transmitted to cloud

---

### Phase 2: Scale to Production Data [Months 3-5]

**Goals:**
- Ingest full 600GB dataset
- Optimize for sub-second performance
- Implement advanced workflows

**Deliverables:**
- Data migration pipeline (600GB → PostgreSQL)
- Vector embedding pipeline (text → Qdrant)
- Semantic chunking (512-token overlapping chunks)
- Metadata tagging (access control, dates, affiliations)
- Advanced indexing strategies
- Autonomous error recovery & retry logic
- Performance optimization (caching, query tuning)
- Role-based access control (RBAC)
- Prototype UI (Streamlit/Gradio)

**Success Criteria:**
- All 600GB indexed and searchable
- Query latency <1 second (95th percentile)
- System handles complex multi-hop queries
- Reliable error recovery
- Role-based filtering works correctly

---

### Phase 3: Production Hardening & Deployment [Months 6-8]

**Goals:**
- Deploy production system
- Security audit & validation
- Strategic pitch finalization

**Deliverables:**
- Kong AI Gateway (security perimeter)
- Production-grade UI (React.js)
- Dynamic data visualizations
- Comprehensive RBAC
- Immutable audit system (cryptographic hashes)
- PII tokenization/FPE implementation
- Adversarial testing (red teaming)
- Load testing (1000+ concurrent users)
- User acceptance testing (all 3 personas)
- Technical documentation
- Strategic proposal deck
- Deployment on sovereign bare-metal

**Success Criteria:**
- Zero vulnerabilities in security audit
- Handles production traffic load
- Intuitive UI for all user types
- Complete audit trail integrity
- Government approval for deployment

---

## TECHNOLOGY STACK

### Core Infrastructure
- **Agent Framework**: LangGraph
- **Relational DB**: PostgreSQL
- **Vector DB**: Qdrant
- **API Gateway**: Kong AI Gateway
- **Embedding**: HuggingFace TEI / local models
- **Local SLM**: Llama 3 (8B quantized)
- **Cloud LLM**: Gemini 2.5 Pro / Claude Sonnet 4
- **Audit**: Langfuse
- **UI**: Streamlit → React.js
- **Security**: Microsoft Presidio (PII detection)

---

## SECURITY & SOVEREIGNTY

### Zero-Leakage Architecture
- Data on bare-metal Indian servers
- Network-level blocking of uploads
- Metadata-only to cloud LLMs
- Full audit trails
- Multi-layer defense (physical, network, app, data)

### Access Control
- RBAC at application & database level
- Permissions injected into vector search queries
- Role-based data filtering

### Audit & Compliance
- Immutable logging (all agentic decisions)
- Cryptographic hashes for tamper-evidence
- DPDP Act 2023 compliance
- Network traffic monitoring

---

## DATA PIPELINE SPECS

### Structured Data (PostgreSQL)
- Tables: researchers, labs, projects, institutions, funding
- ACID compliance
- Advanced indexing (B-tree, GIN)
- Connection pooling

### Unstructured Data (Qdrant)
- Semantic chunking: 512 tokens, 128 token overlap
- Embedding model: BAAI/bge-large-en or similar
- HNSW indexing
- Metadata per vector: access labels, dates, affiliations, categories
- One-stage filtering (performance critical)

### Data Quality
- Duplicate detection
- Normalization (names, institutions, domains)
- Missing data handling
- Regular validation checks

---

## API DESIGN

### Core Endpoints
```
POST /query
{
  "query": "string",
  "persona": "researcher|government|industry",
  "filters": {...}
}

Response:
{
  "results": [...],
  "audit_log_id": "uuid",
  "processing_time": 0.432
}
```

### Admin Endpoints
```
GET /audit/{log_id} - Retrieve audit trail
POST /data/ingest - Ingest new data
GET /health - System health status
```

---

## TESTING STRATEGY

### Unit Tests
- Text-to-SQL generation
- Vector similarity search
- Role-based filtering
- API endpoint validation

### Integration Tests
- End-to-end query flow
- Multi-hop reasoning
- Audit trail generation
- RBAC enforcement

### Security Tests
- Prompt injection attempts
- Data exfiltration attempts
- Authorization bypass
- Network monitoring for leaks

### Performance Tests
- Load: 1000+ concurrent users
- Latency: 95th percentile measuring
- Stress: 10x expected load
- Soak: 72-hour continuous operation

---

## DELIVERABLES

### Technical
1. Working platform (600GB searchable)
2. Zero-leakage architecture
3. Complete audit system
4. Role-based access control
5. Production-grade UI
6. API documentation

### Documentation
1. Technical architecture report
2. Security audit documentation
3. User manuals (3 personas)
4. Deployment guide
5. Maintenance procedures
6. Knowledge graph schema

### Strategic
1. Pitch deck (national infrastructure)
2. Proposal for scale to other institutions
3. Positioning as reference architecture
4. Academic publication outline

---

## SUCCESS METRICS

### Technical
- Latency: <1s for 95% queries
- Availability: 99.9% uptime
- Accuracy: >98% factual consistency
- Security: Zero leakage incidents
- Audit: 100% traceability

### User
- Query success rate: >90%
- Satisfaction: >85%
- Adoption: 500+ active users (Q1)
- Support tickets: <5% technical issues

### Strategic
- Government funding: 40+ crore secured
- Scale: 5+ institutions (18 months)
- Publications: 3+ academic papers
- Recognition: National media coverage

---

## RESOURCE REQUIREMENTS

### Infrastructure
- Servers: High-performance multi-core CPUs
- RAM: 128-256GB minimum
- Storage: NVMe SSDs (600GB + indexes)
- Network: High bandwidth, secure

### Team
- 3-4 Backend Engineers (Python, databases)
- 1-2 Database specialists
- 1 DevOps/Security Engineer
- 1-2 Frontend Engineers
- 1 Project Manager
- Faculty technical advisor

### Estimates
- Development: 8 months
- Team size: 6-8 people
- Infrastructure setup: 2-4 weeks
- Data ingestion: 4-6 weeks

---

## RISKS & MITIGATION

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Data leakage | Low | Critical | Multi-layer security, zero-trust, audits |
| Performance degradation | Medium | High | Optimization, caching, load balancing |
| Stakeholder rejection | Medium | High | Regular demos, clear ROI, political alignment |
| Technical complexity | Medium | Medium | Phased approach, expert consultation, tests |
| Resource constraints | Low | Medium | Clear roadmap, student team, faculty guidance |

---

## NEXT ACTIONS (IMMEDIATE)

1. **Approve project plan** (this document)
2. **Form project team** (identify engineers)
3. **Setup development environment** (PostgreSQL, Qdrant, LangGraph)
4. **Select PoC data subset** (10GB representative sample)
5. **Configure cloud API access** (Gemini/Claude)
6. **Create GitHub repository** (private, internal)
7. **Establish security protocols** (VPN, access controls)
8. **Schedule stakeholder demo** (Week 6: Phase 1 progress)

---

## BUDGET BREAKDOWN (40 CRORE)

- Infrastructure: ₹15 crore (servers, networking, security)
- Personnel: ₹12 crore (8 months, 6-8 engineers)
- Cloud APIs: ₹8 crore (Gemini/Claude usage)
- Security audit: ₹2 crore (external penetration testing)
- Contingency: ₹3 crore (10% buffer)

---

## GOVERNANCE

- **Project Lead**: IIT Gandhinagar faculty member
- **Technical Lead**: Senior student or research engineer
- **Steering Committee**: Government stakeholders (monthly reviews)
- **Status**: Weekly sprints, bi-weekly demos

---

**Status**: PLAN READY FOR APPROVAL
