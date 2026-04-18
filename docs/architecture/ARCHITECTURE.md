# NRG Architecture Specification v1.0

**Mode Flag**: `SYNTHESIS_MODE = local_slm`  
**Status**: Canonical - Supersedes all prior architecture docs  
**Date**: 2026-04-18

---

## 1. Executive Decision

**Synthesis runs locally. This is the single source of truth.**

| Mode | Implementation | Rationale |
|------|---------------|-----------|
| `local_slm` | Llama 3 8B (local execution) | ✅ Data never leaves boundary |
| `cloud_llm_facts_only` | ❌ Rejected | Raw facts egresses to cloud |

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  PRESENTATION LAYER                   │
│  React.js / Streamlit                              │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                   API GATEWAY                      │
│  Kong Gateway - DLP, Rate Limit, Audit           │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                ORCHESTRATION LAYER                  │
│  LangGraph - Query → Skill → Execute → Verify       │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────┬────────────────────────────┐
│    TOOL SKILLS       │      RETRIEVAL             │
│  Text-to-SQL         │  RAG (Qdrant)             │
│  Local Execution    │  Context Retrieval        │
└──────────────────────┴────────────────────────────┘
                            ↓
┌──────────────────────┬────────────────────────────┐
│   POSTGRESQL         │      QDRANT              │
│  Researchers        │  Publications             │
│  Projects, Labs    │  Abstracts, Embeddings   │
└──────────────────────┴────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│               REASONING LAYER (Local)               │
│  Llama 3 8B (quantized) - Local Synthesis Only    │
│  ⚠️ NO external LLM receives research data      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Execution Flow

### Step-by-Step (local_slm mode)

| Step | Actor | What Happens | Egress |
|------|-------|-------------|--------|
| 1 | User | Query submitted | → Gateway |
| 2 | Gateway | PII detection, rate limiting | None |
| 3 | LangGraph | Intent disambiguation, skill routing | None |
| 4 | Cloud LLM | **Only**: semantic planning (metadata) | Metadata + query intent |
| 5 | Local DBs | Execute retrieval (PostgreSQL + Qdrant) | None |
| 6 | Local SLM | Synthesize facts → structured output | None |
| 7 | Local Verification | Cross-reference claims with source | None |
| 8 | User | Verified response | ← Gateway |

### What NEVER leaves local boundary

- Research data (600GB)
- Retrieved facts/chunks
- Synthesized content
- Researcher PII

### What CAN leave (sanitized)

- Query intent (embedded)
- Execution plans (JSON)
- Performance metrics

---

## 4. Threat Model (STRIDE)

| Threat | Attack Vector | Mitigation |
|--------|-------------|------------|
| **Spoofing** | Fake user auth | MFA + RBAC |
| **Tampering** | DB injection | Read-only sandbox, WAF |
| **Repudiation** | Missing logs | Immutable audit (Langfuse) |
| **Information Disclosure** | Data exfiltration | **Local SLM only** |
| **Denial of Service** | Query flood | Rate limiting |
| **Elevation of Privilege** | Role escalation | RBAC enforcement |

### Data Flow Trust Boundaries

```
[User] → [Gateway] → [Orchestrator] → [Local DBs] → [Local SLM] → [User]
                ↓
          [Cloud LLM] ← ONLY metadata/query intent
```

---

## 5. Configuration

```yaml
# config.yaml
synthesis:
  mode: local_slm
  model: llama3-8b-quantized
  device: gpu  # or cpu

security:
  egress_blocked: true
  cloud_llm_data: never
  audit_immutable: true

data_residency:
  region: IN-GJ  # Gujarat, India
  physically_isolated: true
```

---

## 6. Superseded Documents

| Document | Status | Replacement |
|----------|--------|--------------|
| `Sovereign_AI_Protocols_Clean.md` | ⚠️ Superseded | This doc |
| `Sovereign_Infrastructure_Blueprint.md` | ⚠️ Superseded | This doc |
| `docs/technical/architecture_report_final.md` | ⚠️ Superseded | This doc |

**Note**: Prior docs contradicted on synthesis location (cloud vs. local). This doc resolves to `local_slm`.

---

## 7. Success Criteria

- [ ] One canonical architecture doc exists
- [ ] Zero contradictions in architecture decisions
- [ ] SYNTHESIS_MODE = local_slm enforced in config
- [ ] STRIDE threat model documented
- [ ] Data-flow diagram shows all boundaries

---

*This document is the single source of truth for NRG architecture.*