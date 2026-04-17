#!/usr/bin/env python3
"""
Neo4j Schema Definition for National Researcher Graph Knowledge Graph
Defines node types, relationship types, and constraints for the KG
"""

# Node Constraints
CREATE CONSTRAINT researcher_id_unique IF NOT EXISTS
FOR (r:Researcher) REQUIRE r.researcher_id IS UNIQUE;

CREATE CONSTRAINT institution_id_unique IF NOT EXISTS
FOR (i:Institution) REQUIRE i.institution_id IS UNIQUE;

CREATE CONSTRAINT publication_id_unique IF NOT EXISTS
FOR (p:Publication) REQUIRE p.publication_id IS UNIQUE;

CREATE CONSTRAINT lab_id_unique IF NOT EXISTS
FOR (l:Lab) REQUIRE l.lab_id IS UNIQUE;

CREATE CONSTRAINT funding_id_unique IF NOT EXISTS
FOR (f:Funding) REQUIRE f.funding_id IS UNIQUE;

# Node Types with Properties
// Researchers
(:Researcher {
    researcher_id: STRING,
    name: STRING,
    email: STRING,
    phone: STRING,
    orcid: STRING,
    state: STRING,
    research_area: STRING,
    year_joined: INTEGER,
    created_at: DATETIME,
    updated_at: DATETIME
});

// Institutions
(:Institution {
    institution_id: STRING,
    name: STRING,
    type: STRING, // university, lab, company, etc.
    state: STRING,
    country: STRING,
    founded_year: INTEGER,
    website: STRING,
    created_at: DATETIME,
    updated_at: DATETIME
});

// Publications
(:Publication {
    publication_id: STRING,
    title: STRING,
    abstract: STRING,
    venue: STRING,
    year: INTEGER,
    doi: STRING,
    pmid: STRING,
    created_at: DATETIME,
    updated_at: DATETIME
});

// Labs
(:Lab {
    lab_id: STRING,
    name: STRING,
    institution_id: STRING, // FK to Institution
    research_area: STRING,
    established_year: INTEGER,
    website: STRING,
    created_at: DATETIME,
    updated_at: DATETIME
});

// Funding
(:Funding {
    funding_id: STRING,
    researcher_id: STRING, // FK to Researcher
    institution_id: STRING, // FK to Institution
    agency: STRING,
    amount: FLOAT,
    start_date: DATE,
    end_date: DATE,
    title: STRING,
    created_at: DATETIME,
    updated_at: DATETIME
});

// Relationship Types
// Researcher -> Institution (affiliation)
(:Researcher)-[:AFFILIATED_WITH {
    start_date: DATE,
    end_date: DATE,
    position: STRING
}]->(:Institution);

// Researcher -> Publication (authorship)
(:Researcher)-[:AUTHORED {
    author_order: INTEGER
}]->(:Publication);

// Researcher -> Lab (membership)
(:Researcher)-[:MEMBER_OF {
    start_date: DATE,
    end_date: DATE,
    role: STRING // PI, postdoc, student, collaborator
}]->(:Lab);

// Researcher -> Researcher (collaboration/co-authorship)
(:Researcher)-[:COLLABORATES_WITH {
    strength: FLOAT, // based on co-authorship count
    first_collab_year: INTEGER,
    last_collab_year: INTEGER
}]->(:Researcher);

// Lab -> Institution (location)
(:Lab)-[:LOCATED_AT]->(:Institution);

// Publication -> Venue (journal/conference)
(:Publication)-[:PUBLISHED_IN]->(:Venue);

// Funding -> Researcher (funded_by)
(:Funding)-[:FUNDED_BY]->(:Researcher);

// Funding -> Institution (administered_by)
(:Funding)-[:ADMINISTERED_BY]->(:Institution);

// Researcher -> Researcher (mentorship)
(:Researcher)-[:MENTORED {
    start_date: DATE,
    end_date: DATE
}]->(:Researcher);

// Lab -> Lab (collaboration)
(:Lab)-[:COLLABORATES_WITH {
    start_date: DATE,
    end_date: DATE,
    project_count: INTEGER
}]->(:Lab);

// Publication -> Publication (citation)
(:Publication)-[:CITES]->(:Publication);

// Researcher -> Keyword (research_interest)
(:Researcher)-[:INTERESTED_IN {
    strength: FLOAT
}]->(:Keyword);

// Publication -> Keyword (topic)
(:Publication)-[:HAS_KEYWORD]->(:Keyword);

// Lab -> Keyword (specialization)
(:Lab)-[:SPECIALIZES_IN]->(:Keyword);

// Institution -> Keyword (focus_area)
(:Institution)-[:FOCUSES_ON]->(:Keyword);

// Venue Type
(:Venue {
    name: STRING,
    type: STRING, // journal, conference, workshop
    impact_factor: FLOAT,
    issn: STRING
});

// Keyword
(:Keyword {
    keyword: STRING,
    category: STRING, // method, domain, technique, etc.
    created_at: DATETIME
});

// Indexes for Performance
CREATE INDEX researcher_state IF NOT EXISTS
FOR (r:Researcher) ON (r.state);

CREATE INDEX researcher_research_area IF NOT EXISTS
FOR (r:Researcher) ON (r.research_area);

CREATE INDEX institution_type IF NOT EXISTS
FOR (i:Institution) ON (i.type);

CREATE INDEX publication_year IF NOT EXISTS
FOR (p:Publication) ON (p.year);

CREATE INDEX publication_venue IF NOT EXISTS
FOR (p:Publication) ON (p.venue);

CREATE INDEX lab_research_area IF NOT EXISTS
FOR (l:Lab) ON (l.research_area);

CREATE INDEX funding_agency IF NOT EXISTS
FOR (f:Funding) ON (f.agency);

CREATE INDEX funding_year IF NOT EXISTS
FOR (f:Funding) ON (f.start_date);

CREATE INDEX keyword_name IF NOT EXISTS
FOR (k:Keyword) ON (k.keyword);

CREATE INDEX venue_type IF NOT EXISTS
FOR (v:Venue) ON (v.type);

// Composite Indexes
CREATE INDEX researcher_institution_state IF NOT EXISTS
FOR (r:Researcher) ON (r.state, r.research_area);

CREATE INDEX publication_year_venue IF NOT EXISTS
FOR (p:Publication) ON (p.year, p.venue);

CREATE INDEX lab_institution_research_area IF NOT EXISTS
FOR (l:Lab) ON (l.institution_id, l.research_area);