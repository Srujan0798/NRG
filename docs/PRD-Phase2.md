# NRG Phase 2 PRD — Product Requirements Document

**Version:** 2.0  
**Date:** 2026-04-21  
**Status:** Draft

---

## 1. Executive Summary

Phase 2 of NRG adds fine-tuning capability, knowledge graph expansion, and multi-language support to the platform.

---

## 2. Phase 2 Features

### 2.1 Fine-Tuning Pipeline

| Feature | Description | Priority |
|---------|-------------|----------|
| Domain adapter | Fine-tune embedding model on Indian research corpus | P0 |
| Downstream classifier | Train topic/classifier layers | P1 |
| Evaluation harness | Benchmark fine-tuned vs base model | P1 |

**Technical Approach:**
- Use LoRA adapters on `bge-m3` base model
- Training data: 50K labeled research abstracts
- Metrics: retrieval recall@10, reranking NDCG

### 2.2 Knowledge Graph Expansion

| Feature | Description | Priority |
|---------|-------------|----------|
| Neo4j migration | Move from simple graph to full RDF | P1 |
| Dynamic relationships | Edge weights update from query patterns | P2 |
| Recommendation engine | "Similar papers" + "Collaborators" | P2 |

**Data Model:**
```python
{
  "nodes": {
    "researchers": {"h_index", "citations", "collaborations"},
    "publications": {"venue", "citations", "topics"},
    "institutions": {"state", "tier", "lab_count"},
    "projects": {"funding", "duration", "status"}
  },
  "edges": {
    "authored": {"author_order", "corresponding"},
    "cited": {"citation_count"},
    "funded_by": {"amount", "fiscal_year"},
    "affiliated_with": {"since", "role"}
  }
}
```

### 2.3 Multi-Language Support

| Language | Coverage | Priority |
|----------|----------|----------|
| English | 100% | — |
| Hindi | Query → Response | P0 |
| Regional (3 target languages) | Query → Response | P1 |

**Translation Approach:**
- Query: ` IndicTrans` → English → process
- Response: English → `mBART-50` → Hindi/Devanagari

---

## 3. Technical Requirements

### 3.1 Infrastructure

| Component | Phase 1 | Phase 2 |
|-----------|---------|---------|
| Database | PostgreSQL 16 | PostgreSQL 16 + Neo4j |
| GPU | 1x A100 | 4x A100 |
| Storage | 100GB | 500GB |
| Embedding retraining | — | Weekly batch |

### 3.2 Model Registry

```
Model           | Type        | Use Case
----------------|-------------|------------------
bge-m3-base    | Embedding   | Baseline retrieval
bge-m3-finetune| Fine-tuned  | Phase 2 retrieval  
gemma-2-9b     | Synthesis   | Hindi generation
phi-3.5       | Fallback    | Offline mode
```

---

## 4. User Stories

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| F1 | As a researcher, I want Hindi responses | Query in Hindi returns Hindi response |
| F2 | As a researcher, I want AI recommendations | "Similar papers" shows 5 relevant papers |
| F3 | As government, I want entity resolution | Researcher merge shows unified profile |
| F4 | As admin, I want fine-tuning metrics | Dashboard shows retrain impact |

---

## 5. Timeline & Budget

| Milestone | Target | Budget (₹) |
|-----------|--------|------------|
| Fine-tuning pipeline | Q3 2026 | 15L |
| Neo4j migration | Q4 2026 | 10L |
| Hindi support | Q3 2026 | 8L |
| **Total Phase 2** | **Q1 2027** | **33L** |

---

## 6. Risks & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Fine-tune overfitting | Medium | High | Early stopping, eval harness |
| Neo4j performance | Low | Medium | Benchmark Q1 |
| Translation quality | Medium | Medium | Human review queue |

---

**Document Owner:** Product Team  
**Review:** Monthly  
**Next Review:** 2026-05-21