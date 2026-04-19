# Sovereign AI Protocols: Technical Blueprint

## Executive Summary

An architectural blueprint for verifiable, traceable research intelligence from India's confidential 600GB research database.

## Core System Architecture: Three-Layered Framework

**Design Philosophy**: Strict separation between data and reasoning. All confidential data remains within secure, local boundaries while leveraging external LLMs solely as analytical engines.

### Three Primary Principles:
1. **Source Verification** - Every claim traced to original record
2. **Auditability** - Complete decision-making trail logged immutably
3. **Transparency** - Provenance communicated explicitly

### System Flow:

```
User Query
    ↓
Orchestration Layer
    ↓
Intent Disambiguation + Skill Routing
    ↓
Local Execution (PostgreSQL / Vector DB)
    ↓
Data Retrieval (with ID logging)
    ↓
External LLM Synthesis (data-only, no context)
    ↓
Post-hoc Verification
    ↓
Structured Output + Audit Trail
```

## Architecture Layers

### Layer 1: Orchestration Layer
**Function**: Central nervous system of agentic platform
- Disambiguates user intent
- Routes requests to appropriate skills
- Manages conversation state
- Coordinates retrieval and synthesis

**Semantic Mapping**: Converts natural language to standardized concepts
- Example: "robotics labs in Gujarat" → `research_area = 'robotics'` + `location = 'Gujarat'`

**Skill Selection**: Two primary skills
1. **Text-to-SQL** - Structured data queries
2. **RAG Module** - Unstructured text analysis using local vector search

### Layer 2: Local Retrieval Layer
**Function**: Secure data access with complete traceability

**Structured Queries**: Text-to-SQL skill generates precise SQL, executed locally
- Results: Limited to matching records only
- No raw documents or schemas transmitted
- Full ID logging for audit trail

**Unstructured Queries**: Local RAG module
- Embedding generation using local model
- Vector search in Qdrant/Milvus database
- Metadata filtering for access control
- Pre-filtering using SQL results for optimization

**Audit Logging**: Immutable records of:
- All retrieved record identifiers
- Exact SQL queries executed
- Vector search parameters
- Creates tamper-evident audit trail

### Layer 3: External Synthesis Layer
**Function**: Intelligence enhancement without data exposure

**Data Payload**: Only retrieved facts sent to cloud LLM
- **NO**: User query, context, or sensitive metadata
- **YES**: Raw data chunks only

**Synthesis Tasks**:
- Summarization
- Comparative analysis
- Insight extraction

**Post-hoc Verification**: Cross-reference LLM claims with source data to eliminate hallucinations

**Chain of Evidence**: Complete trail from query → records → final answer

## Technology Stack

### Recommended Components:

| Component | Technology | Justification |
|-----------|------------|---------------|
| **Agent Orchestration** | LangChain / Semantic Kernel | Mature frameworks for agents, tools/skills, workflow management |
| **Local Relational DB** | PostgreSQL | High-performance, reliable, ACID-compliant for structured metadata |
| **Local Vector DB** | Qdrant / Milvus | Specialized for high-dim vector similarity search on unstructured text |
| **External LLM** | Google Gemini API / Anthropic Claude | State-of-the-art reasoning without on-premise hosting costs |
| **Auditing & Tracing** | Langfuse | Immutable logging of entire agentic process |
| **UI Prototyping** | Streamlit / Gradio | Rapid development for quick iteration |
| **Production UI** | React.js | Flexible, robust framework for user experience |

### Security Tools:
- **Microsoft Presidio**: PII detection/redaction safeguard
- **Hyperledger Fabric**: Cryptographic hashing for log immutability (optional)

## Data Sovereignty Protocol: Zero-Egress Architecture

**Core Principle**: 600GB of confidential data never leaves secure local environment

### How It Works:

1. **Physical Separation**
   - Confidential database in locked server room
   - Only local application code has access
   - No network egress of raw data

2. **Restricted Data Payloads**
   - Only matching result sets transmitted
   - No raw documents, schemas, or metadata
   - Limited to what's absolutely necessary

3. **Mandatory LLM Instructions**
   - Explicit instructions: "Base response ONLY on provided data"
   - Prevent hallucination/fabrication
   - Enforce factual consistency

4. **Robust Auditing**
   - Langfuse traces of entire process
   - Network monitoring for anomalies
   - Immutable logs for verification

### Multi-Layered Defense:

1. **Physical**: Air-gapped/locked servers
2. **Network**: Monitored egress, no data transmission
3. **Application**: RBAC, skill-based access
4. **Data**: Metadata-only to LLM, tokenization
5. **Audit**: Complete traceability

## Role-Based Access: Three User Personas

### Tier 1: Researchers
**Needs**: Granular details for collaboration
**Output**: 
- Direct personnel links
- Lab locations
- Specific project documents
- Low-level data retrieval prioritized

### Tier 2: Government/Policymakers
**Needs**: High-level trends, institutional summaries
**Output**:
- Aggregated reports
- Comparative analyses
- Concise synthesized insights
- Generative layer emphasized

### Tier 3: Industry Collaborators
**Needs**: Applied research partnerships
**Output**:
- Capability mapping
- Contact information
- Technical specifications
- Strategic partnership insights

## Strategic Value Proposition

**Positioning IIT Gandhinagar as Architect of National AI Infrastructure**

### The Narrative:
This is not just a student project - it's the birth of a **national-scale sovereign AI prototype** that can serve as a reference model for other public-sector data initiatives across India.

### National Alignment:
- **India AI Mission**: Data for AI, compute, economic growth
- **Anusandhan NRF (ANRF)**: AI for Science & Engineering mandate
- **Sovereign AI**: Built on Indian data, for Indian needs

### Competitive Advantage:
- "Old way": Manual queries, insecure chatbots, hallucination-prone
- "Our way": Lightning-fast, secure, intelligent, verifiable

### Long-term Vision:
- Blueprint for nationwide network of research intelligence hubs
- Exportable to IITs, NITs, research institutions
- Establishes IIT Gandhinagar as premier secure AI innovation hub

## Implementation Roadmap

### Phase 1: Proof of Concept (Validation)
**Objective**: Validate core architecture feasibility
- **Data**: Select 10GB representative subset
- **Stack**: Setup PostgreSQL + Qdrant locally
- **Skills**: Text-to-SQL + semantic search
- **Orchestration**: LangChain/Kernel with logging
- **Success**: Demonstrate full flow with traceability

### Phase 2: Full Integration & Refinement
**Objective**: Scale to full dataset
- **Migration**: Clean + normalize full 600GB
- **Indexing**: Optimize PostgreSQL and vector indexes
- **Skill Expansion**: Add complex queries, graph traversal
- **UI**: Streamlit/Gradio prototype with role-based views
- **Security**: RBAC implementation, audit system
- **Performance**: Profiling, optimization, caching

### Phase 3: Deployment & Strategic Proposal
**Objective**: Production deployment and positioning
- **Production**: Secure isolated environment
- **Testing**: UAT with all three user groups
- **Documentation**: Technical reports, user guides
- **Pitch**: Strategic proposal for national infrastructure
- **Legacy**: Frame IIT Gandhinagar as pioneer architect

## Success Metrics

### Technical:
- Zero data leakage incidents
- Sub-second query response times
- 99.9% uptime
- Complete audit trail integrity

### User Experience:
- Natural language query success rate >90%
- Structured output satisfaction
- Role-appropriate information delivery

### Strategic:
- Government approval and funding continuation
- Institutional prestige enhancement
- Position as reference architecture for other initiatives

## Core Differentiators

1. **Sovereignty**: Data never leaves controlled environment
2. **Verifiability**: Every output traceable to source
3. **Intelligence**: Layered reasoning, not just retrieval
4. **Security**: Multi-layered defense, zero-trust architecture
5. **Scalability**: Agentic workflow enables complex querying
6. **Role-based**: Three-tiered user experience
7. **Auditability**: Complete, immutable decision trails

---

**Next Step**: Begin Phase 1 - Select representative data subset and validate core architecture
