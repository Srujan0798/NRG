-- Training pairs schema for fine-tuning data capture
-- Phase 1 of Task #22 — The Fine-Tuning Bridge

CREATE TABLE IF NOT EXISTS training_pairs (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    query TEXT NOT NULL,
    tier INTEGER NOT NULL,
    route TEXT NOT NULL,  -- 'text_to_sql', 'rag', 'hybrid'

    -- SQL path fields
    sql_generated TEXT,
    sql_result TEXT,
    sql_row_count INTEGER DEFAULT 0,

    -- RAG path fields
    chunks_retrieved INTEGER DEFAULT 0,
    chunk_ids TEXT,  -- JSON array of chunk IDs
    similarity_scores TEXT,  -- JSON array of scores

    -- Synthesis fields
    response TEXT,
    citations TEXT,  -- JSON array of [cite:pub_id:chunk_id]
    synthesis_method TEXT,  -- 'cloud_llm', 'local_llm', 'rule_based'

    -- Quality signals
    verifier_score REAL DEFAULT 0.0,  -- faithfulness score
    latency_ms INTEGER DEFAULT 0,
    quality_grade TEXT DEFAULT 'ungraded',  -- GOLD/SILVER/BRONZE/REJECT

    -- User feedback (RLHF signal)
    feedback_score INTEGER DEFAULT NULL,  -- 1-5
    feedback_text TEXT DEFAULT NULL,

    -- Export tracking
    exported BOOLEAN DEFAULT FALSE,
    exported_at TEXT DEFAULT NULL,
    export_version TEXT DEFAULT NULL,

    -- PII scrubbing
    pii_scrubbed BOOLEAN DEFAULT FALSE,

    -- Metadata
    session_id TEXT,
    user_id TEXT,
    node_timings TEXT  -- JSON object with per-node timings
);

CREATE INDEX IF NOT EXISTS idx_training_pairs_tier ON training_pairs(tier);
CREATE INDEX IF NOT EXISTS idx_training_pairs_route ON training_pairs(route);
CREATE INDEX IF NOT EXISTS idx_training_pairs_grade ON training_pairs(quality_grade);
CREATE INDEX IF NOT EXISTS idx_training_pairs_timestamp ON training_pairs(timestamp);
CREATE INDEX IF NOT EXISTS idx_training_pairs_exported ON training_pairs(exported);
CREATE INDEX IF NOT EXISTS idx_training_pairs_feedback ON training_pairs(feedback_score) WHERE feedback_score IS NOT NULL;
