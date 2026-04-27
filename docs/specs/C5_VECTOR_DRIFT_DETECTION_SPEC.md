# C5 — Vector Drift Detection Specification

> **Status**: DRAFT (Guru P4, 2026-04-27)
> **Owner**: ML / Data Architecture
> **Cluster Dependency**: YES — requires populated Qdrant (`nrg_research` collection with ≥10k vectors) for baseline establishment
> **SLO Target**: Drift detection latency <5 min, false-positive rate <5%, coverage gap <10%

---

## 1. Objective

Detect when the semantic quality of embeddings in Qdrant degrades relative to a known-good baseline. This covers:
1. **Model drift**: Switching from BAAI/bge-m3 (primary) to ai4bharat/IndicBERTv2-SS (fallback) without explicit flagging
2. **Data drift**: New ingested documents have embedding distributions that diverge from training-time distribution
3. **Language bias drift**: Indic-language queries return worse recall than English queries (embedding space misalignment)

The system must alert when drift exceeds thresholds and automatically fallback or flag results for human review.

---

## 2. Drift Metrics

### 2.1 Cosine Similarity Distribution Drift (`cosine_drift_score`)

**Definition**: Compare the distribution of pairwise cosine similarities within a sample of the current collection against the baseline distribution.

```python
def cosine_drift_score(current_sample: list[Embedding], baseline_sample: list[Embedding]) -> float:
    """
    Returns KL divergence between current and baseline similarity distributions.
    Range: [0, ∞). Threshold: alert if > 0.5.
    """
    current_sims = [cosine_similarity(a, b) for a, b in combinations(current_sample, 2)]
    baseline_sims = [cosine_similarity(a, b) for a, b in combinations(baseline_sample, 2)]
    return kl_divergence(hist(current_sims), hist(baseline_sims))
```

| Threshold | Meaning | Action |
|-----------|---------|--------|
| < 0.2 | Healthy | No action |
| 0.2 – 0.5 | Warning | Log, increase monitoring frequency |
| > 0.5 | Critical | Alert + trigger fallback review |

### 2.2 Coverage Gap (`coverage_gap_score`)

**Definition**: Fraction of baseline query-answer pairs that fail to retrieve the correct document in top-k after a model/data change.

```python
def coverage_gap_score(benchmark_queries: list[Query], top_k: int = 5) -> float:
    """
    Returns 1 - (successful_retrievals / total_queries).
    Range: [0, 1]. Threshold: alert if > 0.10.
    """
```

| Threshold | Meaning | Action |
|-----------|---------|--------|
| < 0.05 | Healthy | No action |
| 0.05 – 0.10 | Warning | Flag for re-indexing review |
| > 0.10 | Critical | Halt ingestion, alert ML team |

### 2.3 Language Bias Drift (`language_bias_score`)

**Definition**: Measure if Indic-language queries (Hindi, Gujarati, Tamil) have systematically lower recall@k than English equivalents.

```python
def language_bias_score(bilingual_queries: list[(EnglishQuery, IndicQuery)], top_k: int = 5) -> float:
    """
    Returns average (english_recall@k - indic_recall@k) / english_recall@k.
    Range: [0, 1]. Threshold: alert if > 0.20.
    """
```

| Threshold | Meaning | Action |
|-----------|---------|--------|
| < 0.10 | Healthy | No action |
| 0.10 – 0.20 | Warning | Log, consider IndicBERT fine-tuning |
| > 0.20 | Critical | Alert + switch to bilingual retrieval mode |

### 2.4 Embedding Model Fingerprint (`model_fingerprint`)

**Definition**: Hash of the model name + revision + pooling strategy. Any change without explicit approval = immediate alert.

```python
model_fingerprint = hashlib.sha256(
    f"{model_name}:{revision}:{pooling}:{vector_dim}".encode()
).hexdigest()[:16]
```

---

## 3. Baseline Establishment

### 3.1 When to Establish Baseline

1. **Initial**: After first 10k vectors ingested into `nrg_research`
2. **After model change**: Explicitly when switching embedding model (e.g., bge-m3 → IndicBERT)
3. **After major data ingestion**: >20% new vectors added in a single batch
4. **Scheduled**: Monthly automatic re-baseline if drift has been < 0.2 for 30 days

### 3.2 Baseline Artifact

Stored in `.cache/reference_centroids.json` (already exists, needs schema update):

```json
{
  "baseline_id": "bl_2026-04-27_bge-m3_v1",
  "created_at": "2026-04-27T00:00:00Z",
  "model_fingerprint": "a1b2c3d4...",
  "vector_count": 19323,
  "sample_size": 1000,
  "centroids": {
    "overall": [0.12, -0.05, ...],
    "by_language": {
      "en": [0.15, -0.03, ...],
      "hi": [0.10, -0.08, ...],
      "gu": [0.08, -0.06, ...]
    },
    "by_domain": {
      "publications": [0.14, -0.04, ...],
      "grants": [0.11, -0.07, ...]
    }
  },
  "similarity_distribution": {
    "mean": 0.72,
    "std": 0.15,
    "p5": 0.45,
    "p95": 0.91,
    "histogram_bins": [...]
  },
  "benchmark_results": {
    "coverage_gap": 0.03,
    "language_bias": 0.08,
    "recall_at_5": 0.87
  }
}
```

### 3.3 Establishment Command

```bash
python scripts/vector_drift_check.py \
  --establish-baseline \
  --collection nrg_research \
  --sample-size 1000 \
  --output .cache/reference_centroids.json
```

---

## 4. Drift Check Execution

### 4.1 Continuous Monitoring (Lightweight)

Run every 5 minutes via cron / K8s CronJob:

```python
# src/monitoring/vector_drift_monitor.py

def lightweight_drift_check() -> DriftReport:
    """
    Fast check: sample 100 random vectors, compare centroid distance.
    Runtime target: <10 seconds.
    """
    current_sample = qdrant.sample(collection="nrg_research", n=100)
    current_centroid = np.mean(current_sample, axis=0)
    baseline_centroid = load_baseline().centroids["overall"]
    
    distance = cosine_distance(current_centroid, baseline_centroid)
    return DriftReport(
        metric="centroid_distance",
        value=distance,
        threshold=0.15,
        status="healthy" if distance < 0.15 else "warning" if distance < 0.25 else "critical"
    )
```

### 4.2 Deep Check (Nightly)

Run once daily via K8s CronJob:

```python
def deep_drift_check() -> FullDriftReport:
    """
    Full check: all 4 metrics, benchmark query suite, model fingerprint.
    Runtime target: <5 minutes.
    """
    report = FullDriftReport()
    report.cosine_drift = cosine_drift_score(sample(1000), baseline_sample(1000))
    report.coverage_gap = coverage_gap_score(benchmark_queries)
    report.language_bias = language_bias_score(bilingual_benchmark)
    report.model_fingerprint = get_current_model_fingerprint()
    report.model_fingerprint_match = report.model_fingerprint == baseline.fingerprint
    return report
```

### 4.3 Alert Routing

| Severity | Channel | SLA |
|----------|---------|-----|
| Critical | PagerDuty + Slack #nrg-alerts + Email | < 2 min |
| Warning | Slack #nrg-ops | < 10 min |
| Healthy | Log only + Grafana annotation | N/A |

---

## 5. Fallback Strategy

### 5.1 Model Drift Detected (Fingerprint Mismatch)

1. **Immediate**: Alert on-call engineer
2. **Auto-action**: Block ingestion until fingerprint manually approved in `.env`
3. **Query path**: Continue serving with current model but flag all responses with `model_drift_warning: true`
4. **Recovery**: Engineer validates new model on benchmark, runs `--establish-baseline`, removes block

### 5.2 Coverage Gap Detected (>10%)

1. **Immediate**: Alert data team
2. **Auto-action**: Switch retrieval to "hybrid mode" (vector + keyword BM25) for 24 hours
3. **Recovery**: Re-index affected documents, re-run baseline, verify coverage_gap < 5%

### 5.3 Language Bias Detected (>20%)

1. **Immediate**: Alert ML team
2. **Auto-action**: Enable "cross-lingual expansion" — translate Indic query to English before embedding, merge results
3. **Recovery**: Fine-tune IndicBERT on research-domain corpus, A/B test against current model

---

## 6. Integration with Existing Stack

| Component | Integration Point |
|-----------|------------------|
| Qdrant | `src/skills/retrieval/qdrant_client.py` — add `sample()` method |
| Embedding | `src/skills/embedding/` — expose `model_fingerprint` property |
| Monitoring | `infrastructure/grafana/` — new dashboard `08_vector_drift.json` |
| Alerting | `infrastructure/prometheus/rules/` — `VectorDriftHigh` alert rule |
| Audit | `src/audit/` — log every drift check result as audit event |
| API | `/health` endpoint — include `vector_drift_status` field |

### 6.1 Health Endpoint Update

```json
{
  "status": "healthy",
  "database": { "status": "healthy", ... },
  "vector_drift": {
    "status": "healthy",
    "last_check": "2026-04-27T10:00:00Z",
    "cosine_drift": 0.08,
    "coverage_gap": 0.03,
    "language_bias": 0.05,
    "model_fingerprint_match": true
  }
}
```

---

## 7. Benchmark Query Suite

Store in `tests/benchmarks/vector_drift_queries.yaml`:

```yaml
benchmarks:
  - id: VD-001
    query_en: "machine learning publications 2023"
    query_hi: "2023 मशीन लर्निंग प्रकाशन"
    expected_ids: ["pub_12345", "pub_12346"]
    domain: publications

  - id: VD-002
    query_en: "IITGN computer science funding"
    query_gu: "IITGN કમ્પ્યુટર સાયન્સ ફંડિંગ"
    expected_ids: ["grant_9876"]
    domain: grants

  # ... 48 more covering all domains and languages
```

**Target**: 50 bilingual pairs, recall@5 ≥ 85% on English, ≥ 75% on Indic.

---

## 8. File Layout

```
src/
  monitoring/
    vector_drift_monitor.py       # lightweight + deep check implementations
    drift_alerter.py              # alert routing logic
    __init__.py

tests/
  monitoring/
    test_vector_drift_monitor.py  # unit tests for drift calculations
    test_drift_alerter.py         # mock alert routing tests

scripts/
  vector_drift_check.py           # CLI: --establish-baseline, --check, --report
  vector_drift_benchmark.py       # CLI: run benchmark suite, compute recall@k

infrastructure/
  grafana/
    dashboards/
      08_vector_drift.json        # Grafana dashboard (new)
  prometheus/
    rules/
      vector_drift.yml            # AlertManager rules (new)

.cache/
  reference_centroids.json        # Baseline artifact (updated schema)
  drift_history.jsonl             # Append-only log of all checks
```

---

## 9. Implementation Phases

### Phase 1: Core Metrics (Week 1)
- Implement `cosine_drift_score`, `coverage_gap_score`, `language_bias_score`
- Create `scripts/vector_drift_check.py` CLI
- Write unit tests

### Phase 2: Baseline + Monitoring (Week 2)
- Run `--establish-baseline` on populated Qdrant
- Implement lightweight check (5-min cron)
- Integrate with `/health` endpoint

### Phase 3: Alerting + Fallback (Week 3)
- Add Grafana dashboard
- Add Prometheus alert rules
- Implement fallback strategies (hybrid retrieval, cross-lingual expansion)

### Phase 4: Benchmark + Evidence (Week 4)
- Build 50-pair bilingual benchmark
- Run full validation, capture evidence
- Seal C5 acceptance

---

## 10. Evidence Checklist

- [ ] `tests/monitoring/test_vector_drift_monitor.py` passes (all metrics)
- [ ] `.cache/reference_centroids.json` created and schema-validated
- [ ] Lightweight check runs in <10s, deep check in <5min
- [ ] Grafana dashboard `08_vector_drift.json` renders all 4 metrics
- [ ] AlertManager fires test alert for synthetic drift
- [ ] Benchmark suite: recall@5 ≥ 85% (EN), ≥ 75% (Indic)
- [ ] `/health` returns `vector_drift` sub-object
- [ ] Evidence folder: `evidence/2026-04-27/C5_vector_drift/`
