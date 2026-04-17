-- Migration: Initial schema setup
-- Description: Create initial database schema for National Research Graph

BEGIN;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create access tier and user role types
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'access_tier') THEN
        CREATE TYPE access_tier AS ENUM ('1', '2', '3');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role') THEN
        CREATE TYPE user_role AS ENUM ('researcher', 'government', 'industry');
    END IF;
END
$$;

-- Core entity tables
CREATE TABLE IF NOT EXISTS institutions (
    institution_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50),
    state VARCHAR(100),
    city VARCHAR(100),
    established_year INTEGER,
    website VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_institutions_state ON institutions(state);
CREATE INDEX IF NOT EXISTS idx_institutions_type ON institutions(type);

CREATE TABLE IF NOT EXISTS researchers (
    researcher_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(50),
    orcid VARCHAR(20),
    scopus_id VARCHAR(20),
    google_scholar_id VARCHAR(50),
    specialization VARCHAR(255),
    current_position VARCHAR(255),
    access_tier access_tier NOT NULL DEFAULT '1',
    institution_id UUID REFERENCES institutions(institution_id),
    created_at TIMESTAMP WITH TIME Z ONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_researchers_institution ON researchers(institution_id);
CREATE INDEX IF NOT EXISTS idx_researchers_specialization ON researchers(specialization);
CREATE INDEX IF NOT EXISTS idx_researchers_name ON researchers(last_name, first_name);

CREATE TABLE IF NOT EXISTS labs (
    lab_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    acronym VARCHAR(20),
    description TEXT,
    research_area VARCHAR(255),
    institution_id UUID REFERENCES institutions(institution_id),
    head_researcher_id UUID REFERENCES researchers(researcher_id),
    established_year INTEGER,
    access_tier access_tier NOT NULL DEFAULT '1',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_labs_institution ON labs(institution_id);
CREATE INDEX IF NOT EXISTS idx_labs_area ON labs(research_area);

CREATE TABLE IF NOT EXISTS researcher_labs (
    researcher_id UUID REFERENCES researchers(researcher_id) ON DELETE CASCADE,
    lab_id UUID REFERENCES labs(lab_id) ON DELETE CASCADE,
    role VARCHAR(100) DEFAULT 'member',
    joined_date DATE DEFAULT CURRENT_DATE,
    is_primary BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (researcher_id, lab_id)
);

CREATE TABLE IF NOT EXISTS publications (
    publication_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(1000) NOT NULL,
    abstract TEXT,
    journal VARCHAR(255),
    conference VARCHAR(255),
    year INTEGER NOT NULL,
    month INTEGER,
    doi VARCHAR(100),
    citation_count INTEGER DEFAULT 0,
    access_tier access_tier NOT NULL DEFAULT '1',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_publications_year ON publications(year);
CREATE INDEX IF NOT EXISTS idx_publications_doi ON publications(doi);

CREATE TABLE IF NOT EXISTS publication_authors (
    publication_id UUID REFERENCES publications(publication_id) ON DELETE CASCADE,
    researcher_id UUID REFERENCES researchers(researcher_id) ON DELETE CASCADE,
    author_order INTEGER NOT NULL,
    corresponding_author BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (publication_id, researcher_id, author_order)
);

CREATE TABLE IF NOT EXISTS publication_topics (
    publication_id UUID REFERENCES publications(publication_id) ON DELETE CASCADE,
    topic_id UUID NOT NULL,
    relevance_score DECIMAL(3,2) DEFAULT 1.0,
    PRIMARY KEY (publication_id, topic_id)
);

CREATE TABLE IF NOT EXISTS funding (
    funding_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    agency VARCHAR(255),
    amount_inr BIGINT,
    start_date DATE,
    end_date DATE,
    status VARCHAR(50),
    principal_investigator_id UUID REFERENCES researchers(researcher_id),
    co_investigators JSONB DEFAULT '[]',
    access_tier access_tier NOT NULL DEFAULT '2',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_funding_pi ON funding(principal_investigator_id);
CREATE INDEX IF NOT EXISTS idx_funding_agency ON funding(agency);
CREATE INDEX IF NOT EXISTS idx_funding_status ON funding(status);

CREATE TABLE IF NOT EXISTS collaborations (
    collaboration_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    type VARCHAR(50),
    description TEXT,
    institution_a_id UUID REFERENCES institutions(institution_id),
    institution_b_id UUID REFERENCES institutions(institution_id),
    start_date DATE,
    end_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_collab_institution_a ON collaborations(institution_a_id);
CREATE INDEX IF NOT EXISTS idx_collab_institution_b ON collaborations(institution_b_id);

CREATE TABLE IF NOT EXISTS topics (
    topic_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    parent_topic_id UUID REFERENCES topics(topic_id),
    level INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_topics_parent ON topics(parent_topic_id);
CREATE INDEX IF NOT EXISTS idx_topics_level ON topics(level);

ALTER TABLE publication_topics ADD CONSTRAINT IF NOT EXISTS fk_publication_topics_topic
    FOREIGN KEY (topic_id) REFERENCES topics(topic_id) ON DELETE CASCADE;

CREATE TABLE IF NOT EXISTS vector_collections (
    collection_name VARCHAR(100) PRIMARY KEY,
    description TEXT,
    dimension INTEGER NOT NULL,
    vector_model VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS vector_metadata (
    metadata_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    collection_name VARCHAR(100) REFERENCES vector_collections(collection_name),
    source_type VARCHAR(50) NOT NULL,
    source_id UUID NOT NULL,
    access_tier access_tier NOT NULL,
    institution VARCHAR(255),
    topics TEXT[],
    year_range INTEGER[],
    embedding_version VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(source_type, source_id)
);

CREATE INDEX IF NOT EXISTS idx_vector_metadata_collection ON vector_metadata(collection_name);
CREATE INDEX IF NOT EXISTS idx_vector_metadata_access ON vector_metadata(access_tier);
CREATE INDEX IF NOT EXISTS idx_vector_metadata_institution ON vector_metadata(institution);
CREATE INDEX IF NOT EXISTS idx_vector_metadata_topics ON vector_metadata USING GIN(topics);

CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    role user_role NOT NULL DEFAULT 'government',
    access_tier access_tier NOT NULL DEFAULT '2',
    institution VARCHAR(255),
    researcher_id UUID REFERENCES researchers(researcher_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    failed_login_attempts INTEGER DEFAULT 0,
    last_failed_login TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_tier ON users(access_tier);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);

CREATE TABLE IF NOT EXISTS audit_log (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID,
    query_id UUID NOT NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id UUID,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_log_user ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_log_resource ON audit_log(resource_type, resource_id);

-- Security views
CREATE OR REPLACE VIEW v_researchers_public AS
SELECT researcher_id, first_name, last_name, specialization, 
       current_position, institution_id
FROM researchers
WHERE access_tier = '1';

CREATE OR REPLACE VIEW v_labs_public AS
SELECT lab_id, name, acronym, research_area, institution_id
FROM labs
WHERE access_tier = '1';

CREATE OR REPLACE VIEW v_publications_public AS
SELECT publication_id, title, year, citation_count
FROM publications
WHERE access_tier = '1';

-- Read-only role
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nrg_readonly') THEN
        CREATE ROLE nrg_readonly WITH LOGIN PASSWORD 'nrg_readonly_pass';
    END IF;
END
$$;

GRANT USAGE ON SCHEMA public TO nrg_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO nrg_readonly;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO nrg_readonly;

ALTER DEFAULT PRIVILEGES IN SCHEMA public 
GRANT SELECT ON TABLES TO nrg_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public 
GRANT SELECT ON SEQUENCES TO nrg_readonly;

COMMIT;