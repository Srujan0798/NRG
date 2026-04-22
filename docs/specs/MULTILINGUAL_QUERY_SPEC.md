# Feature Spec: Multi-Language Query Support
**Phase:** Phase 3 (Month 16–20)
**Document Status:** Draft
**Author:** NRG Platform Team

---

## 1. Problem Statement

India has 22 official languages. A government official in Gujarat may prefer to ask questions in Gujarati. A Tamil Nadu researcher may want to query in Tamil. Currently, NRG only accepts English queries.

This is both a **usability gap** and a **sovereignty feature** — a truly Indian research platform should support Indian languages.

---

## 2. Goals

1. **Accept queries in Hindi, Gujarati, Tamil, Telugu, Kannada, Malayalam, Marathi, Bengali, Punjabi, Odia**
2. **Return responses in the same language as the query** (when feasible)
3. **Maintain citation accuracy** — language translation must not distort research facts
4. **Indic text in database** — indexed documents in Indian languages are searchable

---

## 3. Non-Goals

- **Full Indic language NLP** — we are supporting query/response, not building a full Indic language model
- **Transliteration** — we'll support native script, not romanized Hindi (Hinglish)
- **Voice input** — text only in Phase 3
- **Automatic language detection for response** — if user queries in Tamil, we respond in Tamil (when model supports it)

---

## 4. Architecture

### 4.1 Query Translation Pipeline

```
User Query (any Indic language)
        │
        ▼
┌─────────────────────────────────┐
│  Language Detection              │
│  (fasttext, 22 languages)        │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│  Translation to English          │
│  (NLLB-200 or IndicTrans)        │
│  (if language ≠ English)         │
└──────────────┬──────────────────┘
               │
               ▼
    Standard NRG Pipeline
    (planner → router → executor
     → synthesizer → verifier)
               │
               ▼
┌─────────────────────────────────┐
│  Response Translation           │
│  (Back to query language)        │
│  (if language ≠ English)        │
└──────────────┬──────────────────┘
               │
               ▼
    User Response (same language
    as query)
```

### 4.2 When No Translation Needed

```
User Query (English)
        │
        ▼
    Standard NRG Pipeline
        │
        ▼
    User Response (English)
```

**Rule:** If the IndicBERT model (already used for embeddings) indicates the query is primarily in English, skip translation entirely.

### 4.3 Supported Languages

| Language | ISO 639-1 | Script | Translation Model |
|----------|-----------|--------|------------------|
| Hindi | hi | Devanagari | NLLB-200 |
| Gujarati | gu | Gujarati | NLLB-200 |
| Tamil | ta | Tamil | NLLB-200 |
| Telugu | te | Telugu | NLLB-200 |
| Kannada | kn | Kannada | NLLB-200 |
| Malayalam | ml | Malayalam | NLLB-200 |
| Marathi | mr | Devanagari | NLLB-200 |
| Bengali | bn | Bengali | NLLB-200 |
| Punjabi | pa | Gurmukhi | NLLB-200 |
| Odia | or | Odia | NLLB-200 |
| English | en | Latin | (no translation) |

---

## 5. Implementation Components

### 5.1 Language Detection

Already present in `src/skills/rag/embedder.py` — the `_detect_language()` function uses character range detection (Devanagari for Hindi/Marathi, Tamil script for Tamil, etc.).

**Enhancement needed:**
- Add fasttext model (`lid.176.bin`) for mixed-language detection
- Confidence threshold: if > 0.8 confidence and language ≠ English → translate

```python
def detect_language_with_confidence(text: str) -> tuple[str, float]:
    """Returns (language_code, confidence)"""
    # fasttext prediction
    lang, confidence = model.predict(text.replace("\n", " "), k=1)
    lang = lang.replace("__label__", "")
    return lang, confidence
```

### 5.2 Translation Service

```python
class TranslationService:
    def __init__(self):
        self.model_name = "facebook/nllb-200-distilled-600M"
        # Or: "ai4bharat/IndicTrans2-en-indic" (if available)

    def translate(
        self,
        text: str,
        source_lang: str,  # "hi", "ta", etc.
        target_lang: str = "eng_Latn"
    ) -> str:
        """Translate text from source language to target language."""
        # Tokenize → translate → detokenize
        inputs = self.tokenizer(text, return_tensors="pt")
        generated = self.model.generate(**inputs, forced_bos_token_id=...)
        return self.tokenizer.decode(generated[0], skip_special_tokens=True)

    def batch_translate(
        self,
        texts: list[str],
        source_lang: str,
        target_lang: str = "eng_Latn"
    ) -> list[str]:
        """Translate multiple texts in batch."""
```

**Model considerations:**
- `facebook/nllb-200-distilled-600M` — smaller, faster, good quality
- `facebook/nllb-200-1.3B` — larger, better quality, slower
- `ai4bharat/IndicTrans2` — India-specific, potentially better for research domain terms

**Decision:** Start with NLLB-200 distilled (600M) for speed; evaluate IndicTrans2 if quality is insufficient.

### 5.3 Router Enhancement

The existing router (`src/orchestration/nodes/router.py`) must handle Indic queries:

```python
def _classify_intent_multilingual(query: str, detected_lang: str) -> str:
    """Classify intent for Indic language queries."""
    if detected_lang != "en":
        # Translate routing keywords only
        routing_keywords = {
            "hi": {"खोजें": "find", "सूची": "list", "कितने": "count"},
            "ta": {"தேடல்": "find", "பட்டியல்": "list", "எத்தனை": "count"},
            # ... etc
        }
        query_for_routing = _translate_routing_keywords(query, detected_lang)
    else:
        query_for_routing = query

    return _classify_intent(query_for_routing)
```

### 5.4 Indic-Optimized Embeddings

The existing `Embedder` class already has `ai4bharat/IndicBERTv2-SS` for Indic language embeddings. The `Research_Documents/` already include Indic documents.

**New requirement:**
- When the user's query is in an Indic language, use `ai4bharat/IndicBERTv2-SS` for embedding (already configured)
- RAG chunks in the same language will have higher similarity

### 5.5 Response Translation

```python
def translate_response(
    response: str,
    source_lang: str = "eng_Latn",
    target_lang: str  # "hi", "ta", etc.
) -> str:
    """Translate the synthesized response back to the query language."""
    if target_lang == "en":
        return response

    # Translate response (avoid translating citation tokens, numbers)
    protected_patterns = [
        r'\[cite:[^\]]+\]',  # citation tokens
        r'\d+\.?\d*',         # numbers
        r'[A-Z][a-z]+ \d{4}',  # year references
    ]
    # ... translate with protected patterns unmolested
```

**Critical:** Citation tokens `[cite:pub_id:chunk_id]` must NOT be translated. Numbers and researcher names should not be translated.

---

## 6. Indic Research Document Indexing

Currently, the Qdrant index uses `all-MiniLM-L6-v2` (English model). For Indic documents:

```python
# In embedder.py
EMBEDDING_MODEL = "BAAI/bge-m3"  # Supports 100+ languages including Indic
FALLBACK_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # English
INDIC_MODEL = "ai4bharat/IndicBERTv2-SS"  # For Indic when primary model supports it
```

**Current status:** `bge-m3` supports 100+ languages including Hindi, Bengali, Tamil, etc. The `Research_Documents/` are already embedded with this model.

**Verification needed:**
```bash
# Check if Indic documents are properly embedded
python -c "
from src.skills.rag.embedder import Embedder
e = Embedder()
# Embed a Hindi query
vec = e.embed(['कृत्रिम बुद्धिमत्ता में शोध'])[0]
print(f'Dimension: {len(vec)}')
# Search Qdrant for Hindi docs
from qdrant_client import QdrantClient
c = QdrantClient('localhost', 6333)
results = c.search('nrg_research', query_vector=vec, limit=3)
print(results[0].payload.get('title'))
"
```

---

## 7. Tier Enforcement Across Languages

The tier rules are the same regardless of language:
- Tier 1 (Researcher): Full details in the response
- Tier 2 (Government): Aggregated stats only
- Tier 3 (Industry): Names + research areas only

**Implementation:** The tier filtering happens at the synthesizer level — it operates on structured data (SQL results, RAG chunks), not on the language of the query. Language translation is transparent to tier enforcement.

---

## 8. Error Handling

| Failure Mode | Behavior |
|-------------|----------|
| Language detection fails | Default to English, try to process |
| Translation to English fails | Try direct Indic embedding; if fails, ask user to query in English |
| Response translation fails | Return English response with note "Response in English due to translation error" |
| Mixed-language query (Hinglish) | Detect dominant language; translate if > 60% Indic |

---

## 9. Performance Requirements

| Metric | Target | Notes |
|--------|--------|-------|
| Language detection latency | < 50ms | Fasttext is fast |
| Translation latency (query) | < 500ms | NLLB-200 600M |
| Translation latency (response) | < 1s | Response is typically 200–500 words |
| P99 end-to-end Indic query | < 5s | Total: detect + translate + query + translate back |
| Indic embedding quality | > 0.7 semantic similarity | On benchmark Indic-QA pairs |

---

## 10. Evaluation

### 10.1 Translation Quality

| Language | BLEU (to English) | BLEU (from English) | Human Score |
|----------|------------------|---------------------|-------------|
| Hindi | > 30 | > 28 | Good |
| Tamil | > 25 | > 22 | Acceptable |
| Gujarati | > 28 | > 26 | Good |
| Telugu | > 25 | > 23 | Acceptable |

**Benchmark:** Translate 100 queries per language → translate back → measure BLEU.

### 10.2 End-to-End Quality

| Metric | Gate | Measurement |
|--------|------|-------------|
| Citation accuracy | ≥ 95% | Citation tokens preserved after translation |
| Tier compliance | 100% | No data leakage in translated responses |
| Intent routing accuracy | ≥ 90% | Same as English baseline |
| User satisfaction | > 4/5 | UAT with native speakers |

---

## 11. Implementation Phases

### Phase 1: Foundation (Month 16)
- [ ] Integrate NLLB-200 distilled (600M) as translation service
- [ ] Language detection with fasttext (with confidence threshold)
- [ ] Query translation (Indic → English)
- [ ] Router enhancement for Indic keywords
- [ ] Indic embedding verification (bge-m3 on existing docs)

### Phase 2: Response Translation (Month 17)
- [ ] Response translation (English → Indic)
- [ ] Citation token protection during translation
- [ ] Tier enforcement verification across languages
- [ ] Error handling: translation failures

### Phase 3: Indic Document Coverage (Month 18)
- [ ] Audit Research_Documents/ for Indic-language content
- [ ] Index Indic documents with bge-m3 embeddings
- [ ] Verify Indic-Indic retrieval quality
- [ ] UAT with native speakers (5 users per major language)

### Phase 4: Polish (Month 19–20)
- [ ] Quality benchmarks per language
- [ ] Fallback to English for low-confidence detection
- [ ] Documentation in all supported languages
- [ ] Production monitoring for translation quality drift

---

## 12. Dependencies

| Dependency | Owner | Blocker For |
|-----------|-------|-------------|
| NLLB-200 model (600M or 1.3B) | Infra | Translation service |
| fasttext model (`lid.176.bin`) | Data | Language detection |
| Indic-QA benchmark dataset | Data | Evaluation |
| Native speaker UAT panel | PM | Phase 3 validation |
| GPU for translation inference | Infra | Production latency |

---

## 13. Open Questions

1. **Which Indic documents do we have?** — We need to audit the 3,310 Research_Documents/ to know which languages are actually present in the corpus. If few documents are in Tamil, Tamil queries won't return good results.
2. **Domain-specific translation vs general NLLB** — NLLB-200 is general-purpose. Research terms like "h-index", "citation", "peer-reviewed" may translate poorly. Should we fine-tune a translation model on research domain data?
3. **Response translation vs multilingual model** — Instead of translate-then-translate, should we try a multilingual base model (like Gemma 7B) that can respond directly in Indic? May be better quality but slower/more expensive.
4. **Which languages to prioritize** — Hindi, Tamil, Gujarati, Telugu, Marathi, Bengali? Start with 3 most-requested based on user research.