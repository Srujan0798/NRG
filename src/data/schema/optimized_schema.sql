-- SQLite Schema for National Research Graph (NRG)
-- Full 50K-record schema with all tables and indexes

-- Institutions Table (kept as-is)
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

-- Researchers Table (expanded)
CREATE TABLE researchers (
    researcher_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    institution_id TEXT NOT NULL,
    state TEXT NOT NULL,
    department TEXT,
    research_area TEXT,
    secondary_research_areas TEXT,
    years_experience INTEGER,
    year_joined INTEGER,
    h_index INTEGER,
    total_funding_received_inr_crores REAL,
    email TEXT,
    phone TEXT,
    orcid TEXT,
    tier_access TEXT,
    access_tier INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Publications Table (expanded)
CREATE TABLE publications (
    publication_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    abstract TEXT,
    authors TEXT,
    researcher_ids TEXT,
    venue TEXT,
    year INTEGER,
    volume TEXT,
    issue TEXT,
    pages TEXT,
    doi TEXT,
    pmid TEXT,
    citations INTEGER,
    impact_factor REAL,
    publication_type TEXT,
    research_area TEXT,
    access_tier INTEGER DEFAULT 1,
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

-- Funding Records Table (expanded)
CREATE TABLE funding_records (
    funding_id TEXT PRIMARY KEY,
    researcher_id TEXT,
    institution_id TEXT,
    project_id TEXT,
    fiscal_year TEXT,
    agency TEXT,
    amount REAL,
    start_date TEXT,
    end_date TEXT,
    title TEXT,
    access_tier INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
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
    institution_id TEXT,
    research_area TEXT,
    research_focus_areas TEXT,
    established_year INTEGER,
    location_state TEXT,
    director_researcher_id TEXT,
    website TEXT,
    access_tier INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
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

-- Projects Table (new)
CREATE TABLE projects (
    project_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    principal_investigator_id TEXT,
    co_pis TEXT,
    start_date TEXT,
    end_date TEXT,
    funding_agency TEXT,
    sanctioned_amount_inr_crores REAL,
    status TEXT,
    research_area TEXT,
    access_tier INTEGER DEFAULT 1
);

-- Patents Table (new)
CREATE TABLE patents (
    patent_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    inventor_ids TEXT,
    applicant_institution TEXT,
    patent_office TEXT,
    application_number TEXT,
    filing_date TEXT,
    grant_date TEXT,
    status TEXT,
    research_area TEXT,
    patent_type TEXT,
    claims_count INTEGER,
    access_tier INTEGER DEFAULT 1
);

-- Collaborations Table (new)
CREATE TABLE collaborations (
    collaboration_id TEXT PRIMARY KEY,
    researcher_ids TEXT,
    partner_institution TEXT,
    partner_country TEXT,
    collaboration_type TEXT,
    start_date TEXT,
    end_date TEXT,
    nature_of_work TEXT,
    funding_amount_inr_crores REAL,
    status TEXT,
    research_area TEXT,
    access_tier INTEGER DEFAULT 1
);

-- Research Documents Table (new)
CREATE TABLE research_documents (
    document_id TEXT PRIMARY KEY,
    title TEXT,
    researcher_ids TEXT,
    affiliation TEXT,
    publication_year INTEGER,
    abstract TEXT,
    keywords TEXT,
    research_area_tags TEXT,
    access_tier INTEGER DEFAULT 1,
    category TEXT,
    file_path TEXT
);

-- Indexes for Performance
CREATE INDEX idx_researchers_institution ON researchers(institution_id);
CREATE INDEX idx_researchers_state ON researchers(state);
CREATE INDEX idx_researchers_research_area ON researchers(research_area);
CREATE INDEX idx_researchers_department ON researchers(department);
CREATE INDEX idx_researchers_year ON researchers(year_joined);
CREATE INDEX idx_researchers_name ON researchers(name);
CREATE INDEX idx_researchers_h_index ON researchers(h_index);
CREATE INDEX idx_researchers_tier_access ON researchers(tier_access);

CREATE INDEX idx_institutions_state ON institutions(state);
CREATE INDEX idx_institutions_type ON institutions(type);

CREATE INDEX idx_publications_year ON publications(year);
CREATE INDEX idx_publications_venue ON publications(venue);
CREATE INDEX idx_publications_doi ON publications(doi);
CREATE INDEX idx_publications_citations ON publications(citations);
CREATE INDEX idx_publications_research_area ON publications(research_area);
CREATE INDEX idx_publications_researcher_ids ON publications(researcher_ids);

CREATE INDEX idx_funding_researcher ON funding_records(researcher_id);
CREATE INDEX idx_funding_institution ON funding_records(institution_id);
CREATE INDEX idx_funding_agency ON funding_records(agency);
CREATE INDEX idx_funding_amount ON funding_records(amount);
CREATE INDEX idx_funding_project_id ON funding_records(project_id);
CREATE INDEX idx_funding_fiscal_year ON funding_records(fiscal_year);

CREATE INDEX idx_labs_institution ON labs(institution_id);
CREATE INDEX idx_labs_research_area ON labs(research_area);

CREATE INDEX idx_projects_pi ON projects(principal_investigator_id);
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_research_area ON projects(research_area);
CREATE INDEX idx_projects_funding_agency ON projects(funding_agency);

CREATE INDEX idx_patents_inventor_ids ON patents(inventor_ids);
CREATE INDEX idx_patents_applicant ON patents(applicant_institution);
CREATE INDEX idx_patents_status ON patents(status);
CREATE INDEX idx_patents_research_area ON patents(research_area);

CREATE INDEX idx_collaborations_researcher_ids ON collaborations(researcher_ids);
CREATE INDEX idx_collaborations_partner ON collaborations(partner_institution);
CREATE INDEX idx_collaborations_country ON collaborations(partner_country);
CREATE INDEX idx_collaborations_status ON collaborations(status);
CREATE INDEX idx_collaborations_research_area ON collaborations(research_area);

CREATE INDEX idx_research_docs_year ON research_documents(publication_year);
CREATE INDEX idx_research_docs_access_tier ON research_documents(access_tier);
CREATE INDEX idx_research_docs_researcher_ids ON research_documents(researcher_ids);

-- Composite Indexes for Common Queries
CREATE INDEX idx_researchers_institution_state ON researchers(institution_id, state);
CREATE INDEX idx_researchers_research_area_year ON researchers(research_area, year_joined);
CREATE INDEX idx_publications_year_venue ON publications(year, venue);

-- Foreign Key Indexes (critical for JOIN performance)
CREATE INDEX idx_researcher_publications_researcher ON researcher_publications(researcher_id);
CREATE INDEX idx_researcher_publications_publication ON researcher_publications(publication_id);
CREATE INDEX idx_publication_keywords_publication ON publication_keywords(publication_id);
CREATE INDEX idx_publication_keywords_keyword ON publication_keywords(keyword_id);
CREATE INDEX idx_researcher_labs_researcher ON researcher_labs(researcher_id);
CREATE INDEX idx_researcher_labs_lab ON researcher_labs(lab_id);

-- Schema migrations tracking
CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TEXT DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO schema_migrations (version) VALUES ('20250421_nrg_full_schema');
