# NRG Sovereign Data Ingest Pipeline

> **Status:** DESIGN READY  
> **Owner:** Data Engineering / DevOps  
> **Cluster Dependency:** PARTIAL — design phase complete; deployment needs sovereign K8s  

## Overview

Pipeline for ingesting the 600 GB research corpus into NRG via sovereign Indian-soil infrastructure. Data arrives via **SFTP** from data providers (IIT-GN, government agencies), is **GPG-decrypted** on-premise, **validated**, and **batch-inserted** into PostgreSQL + Qdrant.

```
Data Provider ──SFTP+GPG──→ NRG Sovereign Edge ──Decrypt──→
    Validate ──→ Postgres (relational) ──→ Qdrant (vectors)
         ↓
    Audit Chain (HMAC-signed per batch)
```

## Architecture

```
┌─────────────────┐     ┌─────────────────────┐     ┌──────────────────┐
│  Data Provider  │────→│  NRG Ingest Gateway │────→│  Decrypt Worker  │
│  (IIT-GN/etc)   │ SFTP│  (sftp.nrg.gov.in)  │     │  (air-gapped)    │
└─────────────────┘     └─────────────────────┘     └──────────────────┘
                                                              │
                              ┌───────────────────────────────┼──────────┐
                              ↓                               ↓          ↓
                        ┌──────────┐                  ┌────────────┐ ┌──────────┐
                        │ Postgres │                  │   Qdrant   │ │  Audit   │
                        │  (raw)   │                  │ (vectors)  │ │  Chain   │
                        └──────────┘                  └────────────┘ └──────────┘
```

## Ingestion Flow

### Phase 1: Secure Transfer (SFTP + GPG)

```
Provider                        NRG Edge
  │                                │
  ├── 1. Encrypt file with NRG public key ──→
  │                                │
  ├── 2. Upload via SFTP to incoming/ ──────→
  │     (chroot jail, no shell access)       │
  │                                │
  │←── 3. NRG returns SHA-256 checksum ──────
  │     (provider verifies integrity)        │
```

**SFTP Configuration:**
- **Host:** `sftp.nrg.gov.in` (Indian-soil only)
- **Port:** 2222 (non-standard to reduce scanning)
- **Auth:** SSH key pairs only — no passwords
- **Chroot:** Each provider gets `/data/incoming/{provider_id}/`
- **Rate limit:** 100 MB/s per connection
- **Max file size:** 50 GB per file
- **Allowed extensions:** `.gpg`, `.pgp`, `.asc`

**Provider Onboarding:**
```bash
# NRG admin generates keypair for provider
scripts/ingestion/onboard_provider.sh --name iitgn --contact data@iitgn.ac.in

# Outputs:
#   - /data/providers/iitgn/public_key.asc   (give to provider)
#   - /data/providers/iitgn/ssh_key.pub      (add to authorized_keys)
#   - /data/incoming/iitgn/                  (chroot directory)
```

### Phase 2: Decryption (Air-Gapped Worker)

```python
# workers/decrypt_worker.py
import gnupg
import hashlib
import os
from pathlib import Path

GPG_HOME = "/var/lib/nrg-gpg"
INCOMING_DIR = "/data/incoming"
DECRYPTED_DIR = "/data/decrypted"
FAILED_DIR = "/data/failed"

def decrypt_file(encrypted_path: Path, provider_id: str) -> Path:
    """Decrypt GPG file and verify checksum."""
    gpg = gnupg.GPG(gnupghome=GPG_HOME)
    
    with open(encrypted_path, "rb") as f:
        result = gpg.decrypt_file(f, output=str(DECRYPTED_DIR / encrypted_path.stem))
    
    if not result.ok:
        # Move to failed, log to audit
        shutil.move(encrypted_path, FAILED_DIR / encrypted_path.name)
        audit_log("DECRYPT_FAILED", provider_id, encrypted_path.name, result.status)
        raise DecryptionError(f"GPG failed: {result.status}")
    
    return DECRYPTED_DIR / encrypted_path.stem
```

**Security constraints:**
- GPG private key stored on HSM or TPM
- Decryption worker has NO network egress
- Decrypted files exist in RAM disk only (tmpfs)
- Auto-delete after 24 hours regardless of outcome

### Phase 3: Validation

```python
# workers/validate_worker.py
from pydantic import BaseModel, validator
import json

class ResearcherRecord(BaseModel):
    name: str
    institution: str
    email: str
    orcid: str | None
    h_index: float | None
    
    @validator("email")
    def email_must_be_institutional(cls, v):
        if not v.endswith((".ac.in", "@gov.in", ".res.in")):
            raise ValueError("Email must be institutional")
        return v

class PublicationRecord(BaseModel):
    title: str
    authors: list[str]
    doi: str | None
    abstract: str
    year: int
    
    @validator("year")
    def year_in_range(cls, v):
        if not (1950 <= v <= 2026):
            raise ValueError("Year out of range")
        return v

def validate_batch(file_path: Path, schema: type) -> list[dict]:
    """Validate JSONL/CSV batch against schema."""
    valid = []
    invalid = []
    
    for line in open(file_path):
        record = json.loads(line)
        try:
            validated = schema(**record)
            valid.append(validated.dict())
        except ValidationError as e:
            invalid.append({"record": record, "error": str(e)})
    
    if invalid:
        audit_log("VALIDATION_PARTIAL", file_path.name, 
                  valid=len(valid), invalid=len(invalid))
    
    return valid, invalid
```

**Validation rules:**
- Schema enforcement (Pydantic)
- PII detection (PAN, Aadhaar patterns) → reject if found in non-government data
- Duplicate detection (DOI, ORCID, title hash)
- Foreign key integrity (institution must exist in `institutions` table)

### Phase 4: Batch Insert (Postgres)

```python
# workers/postgres_ingest.py
import psycopg2
from psycopg2.extras import execute_values

BATCH_SIZE = 1000

def insert_researchers(cursor, records: list[dict]):
    """Batch insert researchers with conflict handling."""
    query = """
        INSERT INTO researchers (name, institution_id, email, orcid, h_index, created_at)
        VALUES %s
        ON CONFLICT (orcid) DO UPDATE SET
            h_index = EXCLUDED.h_index,
            updated_at = NOW()
        RETURNING id
    """
    values = [
        (r["name"], r["institution_id"], r["email"], r["orcid"], r["h_index"], "NOW()")
        for r in records
    ]
    execute_values(cursor, query, values, page_size=BATCH_SIZE)

def insert_publications(cursor, records: list[dict]):
    """Batch insert publications with author linkage."""
    # Similar pattern with ON CONFLICT on DOI
    pass
```

**Insert strategy:**
- Use `COPY FROM` for bulk raw data (fastest)
- Use `execute_values` for relational data with FK checks
- Transaction per batch — rollback on failure
- Update materialized views after each batch

### Phase 5: Vector Indexing (Qdrant)

```python
# workers/qdrant_index.py
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

client = QdrantClient(host="nrg-qdrant", port=6333)

def index_publications(records: list[dict]):
    """Embed and upsert publications to Qdrant."""
    points = []
    for record in records:
        text = f"{record['title']}\n{record['abstract']}"
        vector = embedding_model.encode(text, normalize_embeddings=True).tolist()
        
        points.append(PointStruct(
            id=record["id"],
            vector=vector,
            payload={
                "title": record["title"],
                "doi": record.get("doi"),
                "year": record["year"],
                "authors": record["authors"],
            }
        ))
    
    client.upsert(collection_name="nrg_publications", points=points)
```

**Indexing strategy:**
- Batch size: 100 vectors per upsert
- Parallel workers: 4 (CPU-bound embedding)
- Collection: `nrg_publications` (1024-d, cosine distance)
- HNSW params: `efConstruction=256`, `m=16`

### Phase 6: Audit & Checkpoint

```python
# workers/checkpoint.py
@dataclass
class IngestCheckpoint:
    batch_id: str
    provider_id: str
    file_name: str
    records_total: int
    records_valid: int
    records_invalid: int
    vectors_indexed: int
    pg_rows_inserted: int
    pg_rows_updated: int
    started_at: datetime
    completed_at: datetime
    status: str  # success | partial | failed

def save_checkpoint(cp: IngestCheckpoint):
    """Save checkpoint to audit chain + local file."""
    # 1. Local checkpoint for resume
    with open(f"/data/checkpoints/{cp.batch_id}.json", "w") as f:
        json.dump(asdict(cp), f)
    
    # 2. Audit chain event
    audit_event = {
        "event_type": "BATCH_INGESTED",
        "actor": {"type": "system", "id": "ingest-worker", "tier": "system"},
        "resource": {"type": "batch", "id": cp.batch_id},
        "action": {
            "verb": "INSERT",
            "detail": f"{cp.provider_id}/{cp.file_name}: {cp.records_valid}/{cp.records_total} valid"
        },
    }
    append_to_audit_chain(audit_event)
```

## File Formats

### Input Format (from provider)

```
{provider_id}_researchers_YYYYMMDD.jsonl.gpg
{provider_id}_publications_YYYYMMDD.jsonl.gpg
{provider_id}_grants_YYYYMMDD.jsonl.gpg
{provider_id}_patents_YYYYMMDD.jsonl.gpg
```

Each `.jsonl` contains one JSON object per line.

### Decrypted Format

```jsonl
{"name": "Dr. Ramesh Kumar", "institution": "IIT Bombay", "email": "ramesh@iitb.ac.in", "orcid": "0000-0001-2345-6789", "h_index": 42}
{"name": "Dr. Priya Singh", "institution": "IISc Bangalore", "email": "priya@iisc.ac.in", "orcid": "0000-0002-3456-7890", "h_index": 38}
```

## Throughput Targets

| Phase | Target | Bottleneck |
|-------|--------|------------|
| SFTP transfer | 100 MB/s | Network bandwidth |
| GPG decrypt | 50 MB/s | CPU (single-threaded) |
| Validation | 10k records/sec | CPU (Pydantic) |
| Postgres insert | 50k rows/sec | Disk I/O, indexes |
| Vector embedding | 500 vectors/sec | GPU (A100) |
| Qdrant upsert | 2k vectors/sec | Network + HNSW build |
| **End-to-end** | **~50 GB/day** | Embedding (GPU-bound) |

**600 GB ETA:** ~12 days at steady state (with 2×A100 GPUs)

## Error Handling

| Failure Mode | Handling | Retry |
|--------------|----------|-------|
| SFTP disconnect | Resume from byte offset | Yes, 3× |
| GPG decrypt fail | Move to `/data/failed/`, alert admin | No |
| Schema validation fail | Log invalid rows, ingest valid | Yes, after fix |
| PG connection fail | Backoff 5s, retry batch | Yes, 5× |
| Qdrant timeout | Retry with exponential backoff | Yes, 3× |
| GPU OOM | Reduce batch size, retry | Yes, 2× |

## Sovereign Constraints

1. **Data never leaves Indian soil:** SFTP endpoint on Indian infrastructure only
2. **GPG keys on HSM:** Private key stored on government-approved HSM
3. **No cloud providers:** No AWS S3, Azure Blob, GCP Cloud Storage for staging
4. **Audit everything:** Every batch is HMAC-signed in the audit chain
5. **Retention:** Raw encrypted files kept 90 days, decrypted files deleted immediately after ingest
6. **No foreign LLM APIs:** Embedding runs on local A100 GPUs only

## K8s Deployment

```yaml
# CronJob: runs every 6 hours
apiVersion: batch/v1
kind: CronJob
metadata:
  name: nrg-ingest-pipeline
  namespace: nrg-production
spec:
  schedule: "0 */6 * * *"
  concurrencyPolicy: Forbid
  jobTemplate:
    spec:
      template:
        spec:
          containers:
            - name: ingest
              image: ghcr.io/nrg-india/nrg/ingest:latest
              env:
                - name: INGEST_MODE
                  value: "sftp_poll"
                - name: SFTP_HOST
                  value: "sftp.nrg.gov.in"
                - name: SFTP_PORT
                  value: "2222"
                - name: DECRYPT_ENABLED
                  value: "true"
                - name: GPG_HSM_PATH
                  value: "/dev/tpm0"
              resources:
                requests:
                  cpu: "2"
                  memory: 4Gi
                  nvidia.com/gpu: 1
                limits:
                  cpu: "4"
                  memory: 16Gi
                  nvidia.com/gpu: 1
          restartPolicy: OnFailure
```

## Run Commands

```bash
# Manual trigger (one-off batch)
scripts/ingestion/trigger_ingest.sh --provider iitgn --file researchers_20260425.jsonl.gpg

# Resume failed batch
scripts/ingestion/trigger_ingest.sh --resume --batch-id batch-20260425-001

# Monitor progress
kubectl logs -f job/nrg-ingest-pipeline -n nrg-production

# Check checkpoint
python scripts/ingestion/check_checkpoint.py --batch-id batch-20260425-001
```
