---
name: nrg-embedding-models
description: Use when choosing, validating, tuning, or debugging NRG embedding models, vector drift checks, Qdrant collections, or Indic-language retrieval quality.
---

# NRG Embedding Models Skill

Embedding model selection, vector quality assurance, and language bias detection for the National Research Graph (NRG).

## When to Use

Use this skill when:
- Choosing or switching embedding models for NRG
- Evaluating vector quality for schema-RAG or semantic search
- Detecting language bias in embedding outputs
- Implementing fallback models for Indic languages
- Debugging vector drift (C5 spec)
- Configuring Qdrant collections with optimal distance metrics

## NRG Embedding Architecture

```
Text Input → Primary Model (bge-m3) → 1024-d vector → Qdrant
                ↓ (fallback)
         Indic Model (IndicBERT) → 768-d vector → Qdrant
                ↓ (drift detection)
         Drift Metrics → Grafana → Alert if threshold exceeded
```

## Model Selection

### Primary: BAAI/bge-m3

| Attribute | Value |
|-----------|-------|
| Dimensions | 1024 (dense) + sparse lexical |
| Max tokens | 8192 |
| Languages | 100+ including Hindi, Tamil, Telugu, Bengali |
| License | MIT |
| Size | ~2.3 GB (fp16) |
| Format | GGUF for local inference |

**Why bge-m3 for NRG:**
- Multilingual support covers major Indian languages
- Dense + sparse retrieval (hybrid search)
- Long context (8192 tokens) for research abstracts
- MIT license — no commercial restrictions
- Runs on CPU with GGUF quantization

**Deployment:**
```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("BAAI/bge-m3")

# For retrieval, use instruction prefix
def encode_query(text: str) -> list[float]:
    return model.encode(
        f"Represent this sentence for searching relevant passages: {text}",
        normalize_embeddings=True
    ).tolist()

def encode_passage(text: str) -> list[float]:
    return model.encode(text, normalize_embeddings=True).tolist()
```

### Fallback: IndicBERT / IndicSBERT

| Attribute | Value |
|-----------|-------|
| Dimensions | 768 |
| Languages | 12 Indic languages |
| Best for | Regional language queries when bge-m3 underperforms |
| Trigger | Confidence score < 0.6 from bge-m3 |

```python
indic_model = SentenceTransformer("ai4bharat/indic-sbert")

def get_embedding(text: str, lang_hint: str | None = None) -> list[float]:
    """Route to appropriate model based on language."""
    if lang_hint in INDIC_LANGUAGES:
        return indic_model.encode(text, normalize_embeddings=True).tolist()
    return bge_model.encode(text, normalize_embeddings=True).tolist()
```

## Qdrant Collection Configuration

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

client = QdrantClient(host="localhost", port=6333)

# Primary collection (bge-m3 vectors)
client.create_collection(
    collection_name="nrg_researchers",
    vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
)

# Fallback collection (IndicBERT vectors)
client.create_collection(
    collection_name="nrg_researchers_indic",
    vectors_config=VectorParams(size=768, distance=Distance.COSINE),
)
```

**Distance metric:** Cosine similarity for all NRG collections. Vectors are normalized, so cosine ≈ dot product.

## Vector Quality Checks

### 1. Embedding Consistency Test

```python
def test_embedding_consistency(model, texts: list[str], threshold: float = 0.95):
    """Verify same text produces same embedding (determinism)."""
    embeddings = [model.encode(t, normalize_embeddings=True) for t in texts]
    for emb in embeddings:
        for other in embeddings:
            sim = np.dot(emb, other)
            assert sim >= threshold, f"Inconsistent embedding: {sim}"
```

### 2. Cross-Lingual Alignment Test

```python
# Same meaning in different languages
texts = [
    "machine learning research",           # English
    "मशीन लर्निंग अनुसंधान",              # Hindi
    "யந்திரக் கற்றல் ஆராய்ச்சி",          # Tamil
]

embeddings = [model.encode(t, normalize_embeddings=True) for t in texts]
# All pairwise similarities should be > 0.7 for good cross-lingual alignment
```

### 3. Semantic Coherence Test

```python
# Related concepts should cluster
groups = {
    "ai": ["artificial intelligence", "deep learning", "neural networks"],
    "medicine": ["cardiology", "oncology", "pediatrics"],
    "physics": ["quantum mechanics", "thermodynamics", "optics"],
}

# Intra-group similarity >> inter-group similarity
```

## Language Bias Detection (C5 Spec)

### Metric: Language Bias Ratio

```python
def compute_language_bias_ratio(
    queries: list[str],
    languages: list[str],
    model
) -> dict[str, float]:
    """
    Compare retrieval performance across languages.
    Ratio > 2.0 = significant bias toward high-resource languages.
    """
    results = {}
    baseline_lang = "en"
    baseline_score = evaluate_retrieval(queries, baseline_lang, model)
    
    for lang in languages:
        if lang == baseline_lang:
            continue
        score = evaluate_retrieval(queries, lang, model)
        results[lang] = baseline_score / max(score, 0.001)
    
    return results
```

**Alert threshold:** Any language ratio > 2.0 triggers model retraining or fallback activation.

### Metric: Coverage Gap

```python
def compute_coverage_gap(
    corpus: list[str],
    queries: list[str],
    model,
    k: int = 10
) -> float:
    """
    % of corpus documents never retrieved in top-k across all queries.
    > 10% gap = poor coverage.
    """
    retrieved = set()
    for query in queries:
        q_emb = model.encode(query, normalize_embeddings=True)
        # Search top-k
        hits = search(q_emb, k=k)
        retrieved.update(h.id for h in hits)
    
    return (1 - len(retrieved) / len(corpus)) * 100
```

## Vector Drift Detection (C5)

### Baseline Fingerprint

```python
import hashlib

def compute_model_fingerprint(model_path: str) -> str:
    """Hash of model weights for drift detection."""
    hasher = hashlib.sha256()
    with open(model_path, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()[:16]
```

### Drift Metrics

| Metric | Formula | Alert Threshold |
|--------|---------|-----------------|
| Cosine Drift | `1 - mean(cos_sim(new_emb, baseline_emb))` | > 0.15 |
| Coverage Gap | `% corpus never retrieved` | > 10% |
| Language Bias | `max(lang_ratio)` | > 2.0 |
| Model Fingerprint | `hash(model_file)` | Change = WARN |

## Re-embedding Pipeline

When model changes or drift is detected:

```python
def reembed_corpus(
    collection_name: str,
    new_model,
    batch_size: int = 100
):
    """Re-embed entire corpus with new model."""
    # 1. Create new collection
    new_collection = f"{collection_name}_v{version}"
    
    # 2. Batch re-embed
    for batch in get_batches(documents, batch_size):
        embeddings = new_model.encode(batch.texts, normalize_embeddings=True)
        upload_to_qdrant(new_collection, batch.ids, embeddings, batch.payloads)
    
    # 3. Validate with quality checks
    run_quality_checks(new_collection)
    
    # 4. Atomic swap
    rename_collection(collection_name, f"{collection_name}_old")
    rename_collection(new_collection, collection_name)
    delete_collection(f"{collection_name}_old")
```

## Sovereign Constraints

1. **No OpenAI/foreign APIs:** All embedding inference local on Indian servers
2. **No model telemetry:** No weight uploads, no usage statistics to foreign servers
3. **Model provenance:** All models downloaded once, verified by checksum, stored locally
4. **GGUF quantization:** Acceptable quality tradeoff for sovereign CPU inference
5. **Indic language priority:** If English and Hindi embeddings conflict, Hindi must not be systematically degraded

## Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Embedding latency | <200ms per document | p99 on 1024-d vectors |
| Throughput | >100 docs/sec | Batch size 32, CPU |
| Cross-lingual sim | >0.70 | Same meaning, different language |
| Coverage gap | <5% | Top-10 across 1000 queries |
| Language bias | <2.0 | Max ratio vs English |
