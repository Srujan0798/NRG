-- Production Schema for National Researcher Graph (NRG) 600GB Dataset
-- This schema defines the normalized structure for the full production database

-- Researchers Table
CREATE TABLE researchers (
    researcher_id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    institution_id UUID NOT NULL,
    state VARCHAR(2) NOT NULL,
    research_area VARCHAR(100),
    year_joined INTEGER,
    email VARCHAR(255),
    phone VARCHAR(20),
    orcid VARCHAR(19),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Institutions Table
CREATE TABLE institutions (
    institution_id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50), -- university, lab, company, etc.
    state VARCHAR(2) NOT NULL,
    country VARCHAR(2) DEFAULT 'US',
    founded_year INTEGER,
    website VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Publications Table
CREATE TABLE publications (
    publication_id UUID PRIMARY KEY,
    title TEXT NOT NULL,
    abstract TEXT,
    venue VARCHAR(255),
    year INTEGER,
    doi VARCHAR(100),
    pmid VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Researcher-Publication Relationship (Many-to-Many)
CREATE TABLE researcher_publications (
    researcher_id UUID NOT NULL REFERENCES researchers(researcher_id),
    publication_id UUID NOT NULL REFERENCES publications(publication_id),
    author_order INTEGER,
    PRIMARY KEY (researcher_id, publication_id)
);

-- Funding Records Table
CREATE TABLE funding_records (
    funding_id UUID PRIMARY KEY,
    researcher_id UUID NOT NULL REFERENCES researchers(researcher_id),
    institution_id UUID NOT NULL REFERENCES institutions(institution_id),
    agency VARCHAR(100),
    amount DECIMAL(15,2),
    start_date DATE,
    end_date DATE,
    title VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Keywords Table
CREATE TABLE keywords (
    keyword_id SERIAL PRIMARY KEY,
    keyword VARCHAR(100) UNIQUE NOT NULL
);

-- Publication-Keyword Relationship (Many-to-Many)
CREATE TABLE publication_keywords (
    publication_id UUID NOT NULL REFERENCES publications(publication_id),
    keyword_id INTEGER NOT NULL REFERENCES keywords(keyword_id),
    PRIMARY KEY (publication_id, keyword_id)
);

-- Labs Table
CREATE TABLE labs (
    lab_id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    institution_id UUID NOT NULL REFERENCES institutions(institution_id),
    research_area VARCHAR(100),
    established_year INTEGER,
    website VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Researcher-Lab Relationship (Many-to-Many)
CREATE TABLE researcher_labs (
    researcher_id UUID NOT NULL REFERENCES researchers(researcher_id),
    lab_id UUID NOT NULL REFERENCES labs(lab_id),
    start_date DATE,
    end_date DATE,
    role VARCHAR(100), -- PI, postdoc, student, etc.
    PRIMARY KEY (researcher_id, lab_id)
);

-- Indexes for Performance
CREATE INDEX idx_researchers_institution ON researchers(institution_id);
CREATE INDEX idx_researchers_state ON researchers(state);
CREATE INDEX idx_researchers_research_area ON researchers(research_area);
CREATE INDEX idx_researchers_year ON researchers(year_joined);
CREATE INDEX idx_researchers_name ON researchers(name);

CREATE INDEX idx_institutions_state ON institutions(state);
CREATE INDEX idx_institutions_type ON institutions(type);

CREATE INDEX idx_publications_year ON publications(year);
CREATE INDEX idx_publications_venue ON publications(venue);
CREATE INDEX idx_publications_doi ON publications(doi);

CREATE INDEX idx_funding_researcher ON funding_records(researcher_id);
CREATE INDEX idx_funding_institution ON funding_records(institution_id);
CREATE INDEX idx_funding_agency ON funding_records(agency);
CREATE INDEX idx_funding_amount ON funding_records(amount);

CREATE INDEX idx_labs_institution ON labs(institution_id);
CREATE INDEX idx_labs_research_area ON labs(research_area);

-- GIN Indexes for Full-Text Search
CREATE INDEX idx_publications_abstract_gin ON publications USING gin(to_tsvector('english', abstract));
CREATE INDEX idx_publications_title_gin ON publications USING gin(to_tsvector('english', title));
CREATE INDEX idx_keywords_gin ON keywords USING gin(to_tsvector('english', keyword));

-- Additional Composite Indexes for Common Queries
CREATE INDEX idx_researchers_institution_state ON researchers(institution_id, state);
CREATE INDEX idx_researchers_research_area_year ON researchers(research_area, year_joined);
CREATE INDEX idx_publications_year_venue ON publications(year, venue);

-- Comments
COMMENT ON TABLE researchers IS 'Core researcher information';
COMMENT ON TABLE institutions IS 'Institutional affiliations';
COMMENT ON TABLE publications IS 'Academic publications and papers';
COMMENT ON TABLE funding_records IS 'Grant and funding information';
COMMENT ON TABLE labs IS 'Research laboratories and groups';
COMMENT ON TABLE keywords IS 'Research topics and keywords';