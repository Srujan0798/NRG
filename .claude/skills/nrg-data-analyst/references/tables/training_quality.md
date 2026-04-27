# Training & Quality Tables

This document contains tables for query training pairs, audit events, and platform quality monitoring.

---

## Quick Reference

### Business Context
These tables support the AI/ML pipeline: `training_pairs` captures human feedback for fine-tuning the text-to-SQL model, while `audit_events` provides the immutable compliance trail.

### Standard Filters
```sql
-- For training analysis, focus on graded pairs
WHERE quality_grade IS NOT NULL

-- For audit, respect time ranges
WHERE timestamp >= NOW() - INTERVAL '30 days'
```

---

## Key Tables

### training_pairs
**Location**: `public.training_pairs`
**Description**: Captured query-response pairs for model fine-tuning and quality assessment.
**Primary Key**: `id` (TEXT)
**Update Frequency**: Real-time (every query)

| Column | Type | Description | Notes |
|--------|------|-------------|-------|
| **id** | TEXT | Unique identifier | |
| **timestamp** | TEXT | Query time | UTC; TEXT not TIMESTAMP |
| **query** | TEXT | Natural language question | NOT NULL |
| **tier** | INTEGER | User tier | 1=public, 2=industry, 3=academic, 4=govt |
| **route** | TEXT | Processing path | 'text_to_sql', 'rag', 'hybrid' |
| **sql_generated** | TEXT | Generated SQL | NULL for RAG-only queries |
| **sql_result** | TEXT | Query result | JSON or text |
| **sql_row_count** | INTEGER | Rows returned | 0 if empty or failed |
| **chunks_retrieved** | INTEGER | RAG chunks | 0 for SQL-only |
| **chunk_ids** | TEXT | Chunk IDs | JSON array |
| **similarity_scores** | TEXT | Vector scores | JSON array |
| **response** | TEXT | Final answer | |
| **citations** | TEXT | Citations | JSON array [cite:pub_id:chunk_id] |
| **synthesis_method** | TEXT | How answer built | 'cloud_llm', 'local_llm', 'rule_based' |
| **verifier_score** | REAL | Faithfulness score | 0.0-1.0 |
| **latency_ms** | INTEGER | Total response time | |
| **quality_grade** | TEXT | Post-hoc grade | 'GOLD', 'SILVER', 'BRONZE', 'REJECT' |
| **feedback_score** | INTEGER | User rating | 1-5 or NULL |
| **feedback_text** | TEXT | User comment | |
| **exported** | BOOLEAN | In training set? | |
| **exported_at** | TEXT | Export timestamp | |
| **export_version** | TEXT | Model version | |
| **pii_scrubbed** | BOOLEAN | PII removed? | |
| **session_id** | TEXT | User session | |
| **user_id** | TEXT | Anonymized user | |
| **node_timings** | TEXT | Per-node timing | JSON object |

**Indexes**: `idx_training_pairs_tier`, `idx_training_pairs_route`

**Sample Queries**:
```sql
-- Query success rate by route
SELECT route,
       COUNT(*) AS total,
       COUNT(*) FILTER (WHERE sql_row_count > 0) AS successful,
       ROUND(COUNT(*) FILTER (WHERE sql_row_count > 0) * 100.0 / COUNT(*), 2) AS success_rate
FROM training_pairs
WHERE timestamp >= DATE('now', '-30 days')
GROUP BY route;

-- Quality distribution
SELECT quality_grade, COUNT(*) AS count,
       ROUND(AVG(latency_ms), 0) AS avg_latency_ms
FROM training_pairs
WHERE quality_grade IS NOT NULL
GROUP BY quality_grade
ORDER BY count DESC;

-- User feedback trends
SELECT DATE(timestamp) AS date,
       AVG(feedback_score) AS avg_rating,
       COUNT(*) AS num_ratings
FROM training_pairs
WHERE feedback_score IS NOT NULL
GROUP BY DATE(timestamp)
ORDER BY date;
```

---

### audit_events
**Location**: `public.audit_events`
**Description**: Immutable audit trail of all system events.
**Primary Key**: `event_id` (UUID)
**Update Frequency**: Real-time (every event)

See `nrg-audit-chain` skill for full documentation.

Key fields for analysis:
- `event_type`: 'QUERY_EXECUTED', 'AUTH_FAILURE', 'SCHEMA_CHANGE', etc.
- `actor`: JSON with `type`, `id`, `tier`
- `resource`: JSON with `type`, `id`
- `action`: JSON with `verb`, `detail`
- `timestamp`: Event time
- `hmac`: Verification hash

**Sample Queries**:
```sql
-- Daily query volume by tier
SELECT DATE(timestamp) AS date,
       actor->>'tier' AS tier,
       COUNT(*) AS event_count
FROM audit_events
WHERE event_type = 'QUERY_EXECUTED'
GROUP BY DATE(timestamp), actor->>'tier'
ORDER BY date DESC, event_count DESC;

-- Auth failures (security monitoring)
SELECT DATE(timestamp) AS date,
       context->>'ip_address' AS ip,
       COUNT(*) AS failures
FROM audit_events
WHERE event_type = 'AUTH_FAILURE'
GROUP BY DATE(timestamp), context->>'ip_address'
HAVING COUNT(*) > 10
ORDER BY failures DESC;
```

---

## Common Gotchas

1. **training_pairs.timestamp is TEXT**: Parse with `DATE(timestamp)` or `datetime(timestamp)`.

2. **JSON fields are TEXT**: Use `json_extract()` or parse in application code. PostgreSQL JSON operators (`->`, `->>`) work if stored as JSONB.

3. **Quality grades are sparse**: Most pairs are 'ungraded' (NULL). Only graded pairs are useful for training analysis.

4. **User feedback is voluntary**: Low response rate; don't treat as representative.

5. **PII scrubbing**: `pii_scrubbed = FALSE` means raw query may contain personal data. Handle with care.
