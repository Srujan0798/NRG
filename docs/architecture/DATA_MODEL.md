# NRG Data Model Specification v1.0

## PostgreSQL Schema

### Core Tables

```sql
-- Researchers
CREATE TABLE researchers (
    researcher_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(20),
    orcid VARCHAR(20),
    state VARCHAR(100),
    research_area VARCHAR(255),
    year_joined INTEGER,
    access_tier INTEGER DEFAULT 1 CHECK (access_tier IN (1, 2, 3)),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_researchers_state ON researchers(state);
CREATE INDEX idx_researchers_research_area ON researchers(research_area);
CREATE INDEX idx_researchers_tier ON researchers(access_tier);

-- Institutions
CREATE TABLE institutions (
    institution_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50), -- university, lab, company
    state VARCHAR(100),
    country VARCHAR(100) DEFAULT 'India',
    founded_year INTEGER,
    website VARCHAR(255),
    access_tier INTEGER DEFAULT 1 CHECK (access_tier IN (1, 2, 3)),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_institutions_type ON institutions(type);
CREATE INDEX idx_institutions_state ON institutions(state);

-- Publications
CREATE TABLE publications (
    publication_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(1000) NOT NULL,
    abstract TEXT,
    venue VARCHAR(255),
    year INTEGER,
    doi VARCHAR(50),
    pmid VARCHAR(20),
    access_tier INTEGER DEFAULT 1 CHECK (access_tier IN (1, 2, 3)),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_publications_year ON publications(year);
CREATE INDEX idx_publications_venue ON publications(venue);

-- Labs
CREATE TABLE labs (
    lab_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    institution_id UUID REFERENCES institutions(institution_id),
    research_area VARCHAR(255),
    established_year INTEGER,
    website VARCHAR(255),
    access_tier INTEGER DEFAULT 1 CHECK (access_tier IN (1, 2, 3)),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_labs_institution ON labs(institution_id);
CREATE INDEX idx_labs_research_area ON labs(research_area);

-- Funding
CREATE TABLE funding (
    funding_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    researcher_id UUID REFERENCES researchers(researcher_id),
    institution_id UUID REFERENCES institutions(institution_id),
    agency VARCHAR(255),
    amount DECIMAL(15, 2),
    start_date DATE,
    end_date DATE,
    title VARCHAR(500),
    access_tier INTEGER DEFAULT 1 CHECK (access_tier IN (1, 2, 3)),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_funding_researcher ON funding(researcher_id);
CREATE INDEX idx_funding_institution ON funding(institution_id);
CREATE INDEX idx_funding_agency ON funding(agency);

-- Collaborations
CREATE TABLE collaborations (
    collaboration_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    researcher_id_1 UUID REFERENCES researchers(researcher_id),
    researcher_id_2 UUID REFERENCES researchers(researcher_id),
    strength FLOAT DEFAULT 1.0,
    first_collab_year INTEGER,
    last_collab_year INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_collaborations_r1 ON collaborations(researcher_id_1);
CREATE INDEX idx_collaborations_r2 ON collaborations(researcher_id_2);

-- Keywords
CREATE TABLE keywords (
    keyword_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    keyword VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(50), -- method, domain, technique
    created_at TIMESTAMP DEFAULT NOW()
);

-- Researcher_Keywords (junction)
CREATE TABLE researcher_keywords (
    researcher_id UUID REFERENCES researchers(researcher_id) ON DELETE CASCADE,
    keyword_id UUID REFERENCES keywords(keyword_id) ON DELETE CASCADE,
    strength FLOAT DEFAULT 1.0,
    PRIMARY KEY (researcher_id, keyword_id)
);

-- Audit Log (immutable)
CREATE TABLE audit_log (
    audit_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID,
    query_hash VARCHAR(64),
    table_accessed VARCHAR(100),
    rows_returned INTEGER,
    latency_ms INTEGER,
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_audit_timestamp ON audit_log(timestamp);
CREATE INDEX idx_audit_user ON audit_log(user_id);
```

### Row-Level Security

```sql
-- Enable RLS on all core tables
ALTER TABLE researchers ENABLE ROW LEVEL SECURITY;
ALTER TABLE institutions ENABLE ROW LEVEL SECURITY;
ALTER TABLE publications ENABLE ROW LEVEL SECURITY;
ALTER TABLE labs ENABLE ROW LEVEL SECURITY;
ALTER TABLE funding ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Tier-based access
CREATE POLICY researchers_tier_policy ON researchers
    FOR SELECT USING (access_tier >= current_setting('app.user_tier')::int);

CREATE POLICY institutions_tier_policy ON institutions
    FOR SELECT USING (access_tier >= current_setting('app.user_tier')::int);

-- ... similar for other tables
```

### Qdrant (Vector DB) Schema

```python
# Collection: research_documents
{
    "name": "research_documents",
    "vectors": {
        "size": 1024,
        "distance": "Cosine"
    },
    "payload_schema": {
        "doc_id": "keyword",
        "doc_type": "keyword",  # publication, abstract, project
        "researcher_id": "keyword",
        "institution_id": "keyword",
        "access_tier": "integer",
        "year": "integer",
        "research_area": "keyword"
    }
}

# Collection: researcher_profiles
{
    "name": "researcher_profiles",
    "vectors": {
        "size": 1024,
        "distance": "Cosine"
    },
    "payload_schema": {
        "researcher_id": "keyword",
        "name": "keyword",
        "research_area": "keyword",
        "access_tier": "integer"
    }
}
```

### Foreign Key Constraints Summary

| Table | FK To | Constraint Name |
|-------|-------|----------------|
| labs | institutions | fk_labs_institution |
| funding | researchers | fk_funding_researcher |
| funding | institutions | fk_funding_institution |
| collaborations | researchers (×2) | fk_collab_r1, fk_collab_r2 |
| researcher_keywords | researchers | fk_rk_researcher |
| researcher_keywords | keywords | fk_rk_keyword |

---

*Historical KG alignment note. Current Phase 1 graph behavior is DB-backed through `/query/graph`; optional Neo4j work lives under `experiments/knowledge_graph/`.*
