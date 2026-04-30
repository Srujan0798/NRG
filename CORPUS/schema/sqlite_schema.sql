-- SQLite Schema for National Researcher Graph (NRG)
-- Simplified version for local development

-- Researchers Table
CREATE TABLE researchers (
    researcher_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    institution_id TEXT NOT NULL,
    state TEXT NOT NULL,
    research_area TEXT,
    year_joined INTEGER,
    email TEXT,
    phone TEXT,
    orcid TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Institutions Table
CREATE TABLE institutions (
    institution_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT,
    state TEXT NOT NULL,
    country TEXT DEFAULT 'IN',
    founded_year INTEGER,
    website TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Publications Table
CREATE TABLE publications (
    publication_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    abstract TEXT,
    venue TEXT,
    year INTEGER,
    doi TEXT,
    pmid TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Researcher-Publication Relationship
CREATE TABLE researcher_publications (
    researcher_id TEXT NOT NULL,
    publication_id TEXT NOT NULL,
    author_order INTEGER,
    PRIMARY KEY (researcher_id, publication_id),
    FOREIGN KEY (researcher_id) REFERENCES researchers(researcher_id),
    FOREIGN KEY (publication_id) REFERENCES publications(publication_id)
);

-- Funding Records Table
CREATE TABLE funding_records (
    funding_id TEXT PRIMARY KEY,
    researcher_id TEXT NOT NULL,
    institution_id TEXT NOT NULL,
    agency TEXT,
    amount REAL,
    start_date TEXT,
    end_date TEXT,
    title TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (researcher_id) REFERENCES researchers(researcher_id),
    FOREIGN KEY (institution_id) REFERENCES institutions(institution_id)
);

-- Keywords Table
CREATE TABLE keywords (
    keyword_id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT UNIQUE NOT NULL
);

-- Publication-Keyword Relationship
CREATE TABLE publication_keywords (
    publication_id TEXT NOT NULL,
    keyword_id INTEGER NOT NULL,
    PRIMARY KEY (publication_id, keyword_id),
    FOREIGN KEY (publication_id) REFERENCES publications(publication_id),
    FOREIGN KEY (keyword_id) REFERENCES keywords(keyword_id)
);

-- Labs Table
CREATE TABLE labs (
    lab_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    institution_id TEXT NOT NULL,
    research_area TEXT,
    established_year INTEGER,
    website TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (institution_id) REFERENCES institutions(institution_id)
);

-- Researcher-Lab Relationship
CREATE TABLE researcher_labs (
    researcher_id TEXT NOT NULL,
    lab_id TEXT NOT NULL,
    start_date TEXT,
    end_date TEXT,
    role TEXT,
    PRIMARY KEY (researcher_id, lab_id),
    FOREIGN KEY (researcher_id) REFERENCES researchers(researcher_id),
    FOREIGN KEY (lab_id) REFERENCES labs(lab_id)
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

-- Composite Indexes for Common Queries
CREATE INDEX idx_researchers_institution_state ON researchers(institution_id, state);
CREATE INDEX idx_researchers_research_area_year ON researchers(research_area, year_joined);
CREATE INDEX idx_publications_year_venue ON publications(year, venue);