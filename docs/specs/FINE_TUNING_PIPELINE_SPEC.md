# Feature Spec: Fine-Tuning Pipeline
**Phase:** Phase 2 (Month 9–12)
**Document Status:** Draft
**Author:** NRG Platform Team

---

## 1. Problem Statement

The current RAG+Text-to-SQL+cloud LLM architecture works but has hard scaling limits:

| Problem | Current Approach | Impact |
|---------|-----------------|--------|
| Latency | Every query: embed + search + synthesize | 2–8s per query |
| Cost | Cloud LLM API calls per query | $0.01–0.05/query at scale |
| Reasoning | Can only reason over retrieved chunks | Struggles with multi-hop questions |
| Ambiguity | RAG retrieval quality varies | "Insufficient evidence" responses |

The Core_Idea_Clean.md describes the endgame: **"a model that has deeply internalized the entire dataset — its structure, relationships, and content — the way Claude knows its training data."**

---

## 2. Goals

1. **Reduce per-query latency** from ~3s to <500ms for analytical queries
2. **Reduce cloud LLM API costs** by 80% via local inference
3. **Improve multi-hop reasoning** by giving the model deep schema and relationship knowledge
4. **Achieve "expert salesman" behavior** — instant answers for general questions, precise retrieval only when needed

---

## 3. Non-Goals

- Replace RAG entirely — RAG stays for precision-critical factual lookups
- Train from scratch — fine-tune open-weight base models only
- Deploy a 70B+ model in Phase 2 — start with 8B, validate approach, then scale

---

## 4. Architecture: Two-Brain System

```
USER QUESTION
     │
     ▼
┌─────────────────────────────────────────┐
│        FINE-TUNED LOCAL MODEL           │
│   (Internalized schema + relationships)  │
│                                          │
│  INSTANTLY answers:                     │
│  • "Who is best in hydrogen catalysis?" │
│  • "Compare Gujarat vs Karnataka AI"     │
│  • "What are the main research areas?"   │
│                                          │
│  REQUIRES live retrieval:                │
│  • "Exact h-index of Dr. Patel?"        │
│  • "Dr. Patel's 2024 publications"      │
└──────────────────┬──────────────────────┘
                   │
         Does the question need
         exact/live data?
                   │
        ┌──────────┴──────────┐
        │ NO                  │ YES
        ▼                     ▼
  DIRECT ANSWER         LIVE DB RETRIEVAL
  (from internalized   (SQL precise facts)
   knowledge)
        │                     │
        └──────────┬──────────┘
                   ▼
            MERGED RESPONSE
     (deep insight + exact evidence)
```

---

## 5. Training Data Generation

### 5.1 Query Log Collection (Month 9)

Collect real queries from production for 4–6 weeks:
- All anonymized queries with user_tier, session_id, timestamp
- Include: query text, synthesized response, retrieval sources, user satisfaction rating (if available)
- Target: 10,000+ query-response pairs

### 5.2 Synthetic Q&A Generation (Month 9–10)

Use the current LLM pipeline to generate high-quality training pairs:
- Prompt: "Given this database schema and these sample records, generate 50 natural language questions this data could answer"
- Cover: researcher profiles, publication counts, funding comparisons, collaboration networks, geographic distributions
- Generate 5,000+ synthetic Q&A pairs
- Validate: each pair must have verifiable ground truth

### 5.3 Schema and Relationship Injection

For each Q&A pair, include:
- Table schema (researchers, publications, projects, etc.)
- Relationship edges (who collaborated with whom, which labs belong to which institutions)
- Access tier constraints (what a Tier 2 vs Tier 3 user could ask)
- Citation format examples

### 5.4 Preference Learning Data

For RLHF (Reinforcement Learning from Human Feedback):
- Pairs of answers to the same question (one better than another)
- Criteria: citation accuracy, tier compliance, naturalness, hallucination-free
- Target: 2,000+ preference pairs

---

## 6. Model Selection

| Model | Parameters | Why | Training Approach |
|-------|-----------|-----|-----------------|
| **Llama 3.1 8B** | 8B | Fastest inference, good for experiments | LoRA → QLoRA |
| **Llama 3.1 70B** | 70B | Best reasoning, production target | QLoRA → full fine-tune |
| **Qwen 2.5 72B** | 72B | Excellent at structured data, long context | QLoRA |

**Phase 2 path:** Llama 3.1 8B → validate → Llama 3.1 70B

---

## 7. Training Pipeline

### 7.1 LoRA Adaptation (Week 1–2)
```
Base Model (Llama 3.1 8B)
    │
    ▼
LoRA adapters trained on schema Q&A pairs
    │ (rank=16, alpha=32, dropout=0.1)
    ▼
Merged model with LoRA weights
```

### 7.2 QLoRA Fine-Tuning (Week 3–4)
- 4-bit NF4 quantization
- Gradient accumulation (batch_size=4, gradient_steps=16)
- Learning rate: 2e-4 with cosine schedule
- Training epochs: 3–5 (early stopping on eval loss)
- Compute: 1x A100 (80GB) for 8B model

### 7.3 RLHF Preference Training (Week 5–6)
- Use collected preference pairs
- Reward model training → PPO fine-tuning
- Target: model refuses to hallucinate specific facts without retrieval

### 7.4 Evaluation Gates

| Metric | Gate | Measurement |
|--------|------|-------------|
| Citation faithfulness | ≥ 85% | Eval set of 500 Q&A pairs |
| Tier compliance | 100% | Automated tier-access tests |
| Latency (analytical Q) | < 500ms | Local inference benchmark |
| Hallucination rate | < 5% | Adversarial query test set |
| Retrieval fallback accuracy | ≥ 90% | When model says "I don't know, retrieving..." |

---

## 8. Two-Brain Routing Logic

```python
def route_query(query: str, model) -> "direct" | "retrieve":
    """
    Use the fine-tuned model to decide:
    - "direct": model can answer from internalized knowledge
    - "retrieve": question requires exact/live data
    """
    prompt = f"""
    Question: {query}
    Does this require exact database values (specific names, numbers, dates)?
    Or can it be answered from general research knowledge?

    Answer: direct/retrieve
    Confidence: high/medium/low
    """
    response = model.generate(prompt)
    # Parse response to determine routing
```

---

## 9. Integration with Current Architecture

The fine-tuned model **replaces cloud LLM synthesis only**. All other components remain:

```
Current Pipeline (Phase 1-3):
  executor → synthesizer(CLOUD_LLM) → verifier → END

Phase 2 Pipeline:
  executor → synthesizer(FINE_TUNED_LOCAL) → verifier → END
                              │
                              └── Or: synthesizer(DIRECT) → END (skip retrieval)

RAG and Text-to-SQL stay:
  executor still runs skills → results still go to synthesizer
  Fine-tuned model uses results for precision, internalized knowledge for general answers
```

---

## 10. Security Considerations

| Concern | Mitigation |
|---------|------------|
| Model memorizing training data | RLHF penalty for hallucinating specific facts |
| PII in model weights | Never train on raw PII; use tier-filtered, minimized data only |
| Sovereignty of fine-tuned model | Model stays on-premise; never uploaded to any cloud |
| Tier bypass via prompt injection | System prompt enforces tier; RLHF reinforces |

---

## 11. Rollout Plan

| Phase | Timeline | Milestone |
|-------|----------|-----------|
| Data collection | Month 9, Weeks 1–4 | 10K query logs + 5K synthetic Q&A |
| Training | Month 10, Weeks 1–4 | Llama 3.1 8B fine-tuned and evaluated |
| Shadow mode | Month 11, Week 1 | Fine-tuned model runs parallel to cloud LLM; responses compared |
| Shadow mode | Month 11, Week 2–4 | A/B test: 10% traffic to fine-tuned model |
| Full cutover | Month 12 | Fine-tuned model as primary; cloud LLM as fallback |
| Scale to 70B | Month 12 | Llama 3.1 70B fine-tune begins |

---

## 12. Open Questions

1. **Should we train separate models per tier?** Tier 1, 2, 3 have different data access — one model vs three?
2. **How often to re-train?** As the database updates, the model's knowledge stale. How frequently to update?
3. **Evaluation dataset size** — is 500 Q&A pairs enough to validate, or do we need 5,000?
4. **Qwen vs Llama** — should we evaluate both as base models before committing to one?

---

## 13. Dependencies

| Dependency | Owner | Blocker For |
|-----------|-------|-------------|
| 10K query logs from production | Data Team | Training data generation |
| A100 compute for training | Infra | LoRA → QLoRA training |
| RLHF preference pair labeling | QA | Preference training |
| Tier-filtered training data pipeline | Data Team | Training data generation |
| Model serving infrastructure (vLLM or llama.cpp) | Infra | Production deployment |