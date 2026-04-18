-- NRG Database Seed Schema
-- Loaded by Docker at startup

-- Researchers
CREATE TABLE IF NOT EXISTS researchers (
    researcher_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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

CREATE INDEX IF NOT EXISTS idx_researchers_state ON researchers(state);
CREATE INDEX IF NOT EXISTS idx_researchers_research_area ON researchers(research_area);
CREATE INDEX IF NOT EXISTS idx_researchers_tier ON researchers(access_tier);

-- Institutions
CREATE TABLE IF NOT EXISTS institutions (
    institution_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50),
    state VARCHAR(100),
    country VARCHAR(100) DEFAULT 'India',
    founded_year INTEGER,
    website VARCHAR(255),
    access_tier INTEGER DEFAULT 1 CHECK (access_tier IN (1, 2, 3)),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_institutions_type ON institutions(type);
CREATE INDEX IF NOT EXISTS idx_institutions_state ON institutions(state);

-- Publications
CREATE TABLE IF NOT EXISTS publications (
    publication_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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

CREATE INDEX IF NOT EXISTS idx_publications_year ON publications(year);
CREATE INDEX IF NOT EXISTS idx_publications_venue ON publications(venue);

-- Labs
CREATE TABLE IF NOT EXISTS labs (
    lab_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    institution_id UUID REFERENCES institutions(institution_id),
    research_area VARCHAR(255),
    established_year INTEGER,
    website VARCHAR(255),
    access_tier INTEGER DEFAULT 1 CHECK (access_tier IN (1, 2, 3)),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_labs_institution ON labs(institution_id);
CREATE INDEX IF NOT EXISTS idx_labs_research_area ON labs(research_area);

-- Funding
CREATE TABLE IF NOT EXISTS funding (
    funding_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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

CREATE INDEX IF NOT EXISTS idx_funding_researcher ON funding(researcher_id);
CREATE INDEX IF NOT EXISTS idx_funding_institution ON funding(institution_id);
CREATE INDEX IF NOT EXISTS idx_funding_agency ON funding(agency);

-- Keywords
CREATE TABLE IF NOT EXISTS keywords (
    keyword_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    keyword VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- RLS Policies (Postgres)
ALTER TABLE researchers ENABLE ROW LEVEL SECURITY;
ALTER TABLE institutions ENABLE ROW LEVEL SECURITY;
ALTER TABLE publications ENABLE ROW LEVEL SECURITY;
ALTER TABLE labs ENABLE ROW LEVEL SECURITY;
ALTER TABLE funding ENABLE ROW LEVEL SECURITY;

CREATE POLICY IF NOT EXISTS researchers_select_policy ON researchers
    FOR SELECT USING (access_tier >= 1);

CREATE POLICY IF NOT EXISTS institutions_select_policy ON institutions
    FOR SELECT USING (access_tier >= 1);

CREATE POLICY IF NOT EXISTS publications_select_policy ON publications
    FOR SELECT USING (access_tier >= 1);

CREATE POLICY IF NOT EXISTS labs_select_policy ON labs
    FOR SELECT USING (access_tier >= 1);

CREATE POLICY IF NOT EXISTS funding_select_policy ON funding
    FOR SELECT USING (access_tier >= 1);

-- Sample Data
INSERT INTO researchers (name, email, research_area, state, access_tier) VALUES
    ('Dr. Amit Patel', 'amit.patel@iitgn.ac.in', 'Machine Learning', 'Gujarat', 1),
    ('Dr. Priya Sharma', 'priya.sharma@iitgn.ac.in', 'Robotics', 'Gujarat', 1),
    ('Dr. Raj Gupta', 'raj.gupta@nit.ac.in', 'Sustainable Energy', 'Maharashtra', 1),
    ('Dr. Anjali Mehta', 'anjali.mehta@iitb.ac.in', 'Quantum Computing', 'Maharashtra', 2),
    ('Dr. Vikram Singh', 'vikram.singh@iitd.ac.in', 'AI for Healthcare', 'Delhi', 2)
ON CONFLICT (email) DO NOTHING;

INSERT INTO institutions (name, type, state, access_tier) VALUES
    ('IIT Gandhinagar', 'university', 'Gujarat', 1),
    ('IIT Bombay', 'university', 'Maharashtra', 1),
    ('NIT Surathkal', 'university', 'Karnataka', 1),
    ('IIT Delhi', 'university', 'Delhi', 2),
    ('IIT Madras', 'university', 'Tamil Nadu', 2)
ON CONFLICT DO NOTHING;

INSERT INTO keywords (keyword, category) VALUES
    ('Machine Learning', 'domain'),
    ('Robotics', 'domain'),
    ('Quantum Computing', 'domain'),
    ('Sustainable Energy', 'domain'),
    ('AI for Healthcare', 'domain'),
    ('Neural Networks', 'technique'),
    ('Reinforcement Learning', 'technique'),
    ('Computer Vision', 'technique')
ON CONFLICT (keyword) DO NOTHING;