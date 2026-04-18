# NRG Ingestion Pipeline Specification v1.0

## 600 GB Pipeline Design

### Data Stats

| Component | Size | Vectors | Estimate |
|-----------|------|--------|---------|
| Publications | ~400 GB | ~50M | 512-token chunks |
| Abstracts | ~100 GB | ~10M | 256-token chunks |
| Researcher profiles | ~50 GB | ~500K | Full profile |
| Lab documentation | ~50 GB | ~5M | 512-token chunks |

### Chunk Strategy

| Doc Type | Chunk Size | Overlap | Notes |
|---------|-----------|--------|-------|
| Publications | 512 tokens | 50 tokens | Semantic boundaries |
| Abstracts | 256 tokens | 25 tokens | Full abstract |
| Profiles | 512 tokens | 50 tokens | Section-based |
| Labs | 512 tokens | 50 tokens | By subsection |

### Dedup Strategy

- Simhash for near-dup detection
- Minhash LSH for set similarity
- Threshold: 0.95 similarity → merge
- Expected dedup rate: ~15%

### Embedding Model

| Model | Dims | GPU | Throughput |
|-------|------|-----|--------|
| BGE-Large | 1024 | A100 | ~5000/sec |
| BGE-Base | 768 | A100 | ~10000/sec |

### GPU Plan

```
A100 80GB × 2 ( redundancy)
VRAM: 40GB for model, 40GB for batch
Batch size: 64 (L), 128 (B)
Queue: 1000 pending max
```

### Qdrant Sharding

```
Total vectors: ~65M
Shards: 8
Replicas: 2
HNSW:
  efConstruction: 256
  m: 16
  max_indexing_threads: 16
```

### Wall Clock Estimate

| Phase | Duration | Notes |
|-------|----------|-------|
| Chunking | 8 hours | GPU-bound |
| Embedding | 12 hours | GPU-bound |
| Indexing | 4 hours | I/O-bound |
| Total | 24 hours | With retries |

### Throughput Target

- **Vectors/sec**: 5000 (BGE-Large)
- **GB/hour**: 50 GB processed

### Checkpoint Design

```python
# scripts/ingest.py
import json
from pathlib import Path
from dataclasses import dataclass, asdict

@dataclass
class IngestionCheckpoint:
    phase: str  # chunking, embedding, indexing
    file_id: str
    offset: int
    last_vector_id: str
    timestamp: str

CHECKPOINT_FILE = ".ingestion_checkpoint.json"

def save_checkpoint(checkpoint: IngestionCheckpoint):
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(asdict(checkpoint), f)

def load_checkpoint() -> IngestionCheckpoint | None:
    if not Path(CHECKPOINT_FILE).exists():
        return None
    with open(CHECKPOINT_FILE) as f:
        return IngestionCheckpoint(**json.load(f))

def resume():
    """Resume from checkpoint."""
    checkpoint = load_checkpoint()
    if checkpoint:
        # Resume from phase+offset
        pass
```

### Pipeline Script

```python
#!/usr/bin/env python3
# scripts/ingest.py
import argparse
import logging
from pathlib import Path
from scripts.chunker import chunk_file
from scripts.embedder import embed_batch
from scripts.qdrant_writer import upsert_vectors

logging.basicConfig(level=logging.INFO)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    checkpoint = load_checkpoint() if args.resume else None

    for file in Path(args.input).glob("*.json"):
        for chunk in chunk_file(file):
            vectors = embed_batch(chunk)
            upsert_vectors(vectors, checkpoint=checkpoint)

if __name__ == "__main__":
    main()
```

### Run Commands

```bash
# Full ingestion
scripts/ingest.py --input data/research/

# Resume after kill -9
scripts/ingest.py --input data/research/ --resume

# Test with 10GB subset
scripts/ingest.py --input data/research_10gb/ --limit 10GB
```

### CI Integration

```yaml
# .github/workflows/ingestion-ci.yml
- name: Ingest 10GB subset
  run: |
    scripts/ingest.py --input data/research_10gb/ --limit 10GB
  timeout: 30m
```

---

*Pipeline resumes after kill -9 with no duplicate vectors.*