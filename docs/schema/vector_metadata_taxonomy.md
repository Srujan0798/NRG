# Vector Metadata Taxonomy

## Overview

This document defines the metadata taxonomy for Qdrant vector collections in the National Research Graph. All vectors stored in Qdrant must include the following standardized payload fields to enable filtering, access control, and provenance tracking.

## Payload Schema

### Base Fields (Required for All Collections)

| Field | Type | Description |
|-------|------|-------------|
| `source_type` | string | Entity type: `researcher`, `publication`, `lab`, `funding` |
| `source_id` | string (UUID) | Unique identifier linking to PostgreSQL record |
| `access_tier` | integer | 1, 2, or 3 - controls retrieval based on user tier |
| `institution` | string | Institution name for filtering |
| `created_at` | ISO8601 timestamp | When the record was created |

### Researcher-Specific Fields

| Field | Type | Description |
|-------|------|-------------|
| `first_name` | string | First name |
| `last_name` | string | Last name |
| `specialization` | string | Research area/expertise |
| `topics` | string[] | Array of topic tags |
| `orcid` | string | ORCID identifier (optional) |

### Publication-Specific Fields

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Publication title |
| `abstract` | string | Publication abstract |
| `year` | integer | Publication year |
| `journal` | string | Journal name |
| `doi` | string | Digital Object Identifier |
| `authors` | string[] | Author names |
| `topics` | string[] | Research topics |

### Lab-Specific Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Lab name |
| `acronym` | string | Lab acronym |
| `research_area` | string | Primary research area |
| `institution_id` | UUID | Link to institution |
| `head_researcher` | string | Lab director name |

### Funding-Specific Fields

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Funding title |
| `agency` | string | Funding agency (DST, DB, etc.) |
| `amount_inr` | integer | Grant amount in INR |
| `year_range` | int[2] | [start_year, end_year] |
| `status` | string | active, completed, pending |

## Access Tier Filtering

### Tier 1: Researchers (Full Access)
- Can retrieve: `access_tier = 1, 2, 3`
- Includes: Contact details, ORCID, direct联系方式

### Tier 2: Government/Policymakers (Aggregated)
- Can retrieve: `access_tier = 2, 3`
- Excludes: Personal contact info, ORCID

### Tier 3: Industry (Limited)
- Can retrieve: `access_tier = 3 only`
- Includes: Institution names, research areas only

## Filtering Examples

### Qdrant Filter Queries

```python
# Tier 1 researcher query
filter = {
    "must": [
        {"key": "access_tier", "lte": 1},
        {"key": "topics", "array_contains": "robotics"}
    ]
}

# Tier 2 government query
filter = {
    "must": [
        {"key": "access_tier", "lte": 2},
        {"key": "institution", "match": "IIT*"}
    ]
}
```

## Indexing Strategy

- `access_tier`: Indexed for fast filtering
- `source_type`: Indexed for collection routing
- `institution`: Indexed for institutional queries
- `topics`: GIN indexed for array containment

## Metadata Versioning

Each payload includes:
- `embedding_version`: Model version used
- `created_at`: Timestamp
- `embedding_model`: Model name (e.g., `sentence-transformers/all-MiniLM-L6-v2`)

This enables reprocessing if embedding models are updated.