# ADR-005: Why Qdrant for Vector Search

**Date:** 2026-04-21  
**Status:** Accepted  
**Deciders:** Architecture Team, ML Platform Team  
**Review:** 2026-07-21

---

## Context

NRG requires vector similarity search for:
- **RAG (Retrieval Augmented Generation)**: Finding relevant research papers/context
- **Researcher similarity**: Matching researchers with similar expertise
- **Semantic search**: Natural language query understanding
- **Recommendation engine**: "Similar papers", "Potential collaborators"

We evaluated Qdrant, pgvector (PostgreSQL extension), Weaviate, and Milvus.

---

## Decision

Use **Qdrant** as the primary vector database for production, with SQLite as fallback for development.

---

## Alternatives Considered

| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| **Qdrant** (chosen) | Rust performance, filters, Onyxia compliance | Learning curve | ✅ Accepted |
| pgvector | Single database, PostgreSQL native | Slower on large datasets | ❌ Rejected |
| Weaviate | GraphQL API, built-in modules | Heavy, resource intensive | ❌ Rejected |
| Milvus | Scale, maturity | Complex setup, operational overhead | ❌ Rejected |
| Pinecone | Managed, easy start | Vendor lock-in, expensive at scale | ❌ Rejected |

---

## Rationale

### 1. Performance (Rust-based)

Qdrant is built in Rust, providing:
- 100M+ vector scalability
- Sub-10ms query latency at high throughput
- Memory-mapped storage for large collections

### 2. Filtering Capabilities

Critical for NRG's tier-based access:

```python
# Filter by researcher tier in vector search
client.search(
    collection_name="nrg_research",
    query_vector=embedding,
    query_filter={
        "must": [
            {"key": "access_tier", "match": {"value": 1}},
            {"key": "state", "match": {"value": "Gujarat"}}
        ]
    },
    limit=10
)
```

### 3. Sovereign Deployment

Qdrant can run on-premise (Indian government requirement):
- Docker/Kubernetes deployment
- No data leaves the infrastructure
- Air-gapped operation supported

### 4. Onyxia Compliance

Qdrant is on the [Onyxia](https://onyxia.eu/) approved software list:
- French government AI platform compatibility
- European sovereignty requirements met
- Potential integration with national AI infrastructure

### 5. API Compatibility

```python
# Qdrant client
from qdrant_client import QdrantClient

client = QdrantClient(host="localhost", port=6333)
results = client.search(
    collection_name="nrg_research",
    query_vector=embedding.tolist(),
    limit=5
)
```

---

## Implementation

### Collection Schema

```yaml
collection: nrg_research
vector_size: 1024  # BGE-M3 embeddings
distance: Cosine

payload_indexes:
  - researcher_id (keyword)
  - institution_id (keyword)
  - research_area (keyword)
  - state (keyword)
  - access_tier (integer)
  - year (integer)

optimization:
  vector_index: HNSW
  quantization: scalar (int8)
```

### Ingestion Pipeline

```python
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

model = SentenceTransformer('BAAI/bge-m3')
client = QdrantClient(host="qdrant", port=6333)

def ingest_researcher(researcher):
    embedding = model.encode(researcher["abstract"])
    point = PointStruct(
        id=researcher["id"],
        vector=embedding.tolist(),
        payload={
            "researcher_id": researcher["id"],
            "state": researcher["state"],
            "research_area": researcher["area"],
            "access_tier": researcher["tier"]
        }
    )
    client.upsert(collection_name="nrg_research", points=[point])
```

### Fallback Behavior

```python
# If Qdrant is unavailable
if not qdrant_healthy():
    logger.warning("Qdrant unavailable, using SQL-only fallback")
    results = text_to_sql_skill.execute(
        query, user_tier,
        fallback_mode=True
    )
```

---

## Consequences

### Positive
- High-performance vector search at scale
- Filtering for tier-based access
- Sovereign deployment support
- Onyxia/national AI platform compatibility
- Memory-efficient with quantization

### Negative
- Additional infrastructure component
- Learning curve for vector operations
- Sync complexity with PostgreSQL

### Risks
- Qdrant downtime degrading RAG quality
  - Mitigation: SQL-only fallback, monitoring alerts
- Embedding model drift
  - Mitigation: Regular re-indexing, evaluation metrics

---

## Configuration

```yaml
# docker-compose.yml
qdrant:
  image: qdrant/qdrant:v1.7.0
  ports:
    - "6333:6333"
    - "6334:6334"
  volumes:
    - qdrant_storage:/qdrant/storage
  environment:
    - QDRANT__SERVICE__GRPC_PORT=6334

# Environment
QDRANT_HOST=qdrant
QDRANT_PORT=6333
QDRANT_COLLECTION=nrg_research
QDRANT_VECTOR_SIZE=1024
```

---

## References

- [Knowledge Graph Spec](docs/specs/NEO4J_KNOWLEDGE_GRAPH_SPEC.md)
- [RAG Pipeline](docs/architecture/ORCHESTRATION.md)
- [Vector Metadata Taxonomy](docs/schema/vector_metadata_taxonomy.md)

---

**Reviewed by:** ML Platform Team, Architecture Team  
**Sign-off:** 2026-04-21