# Knowledge Graph Design for National Research Graph (NRG)

## Overview
This document describes the knowledge graph design for the National Research Graph (NRG) Phase 2 implementation. The knowledge graph models complex relationships between researchers, institutions, publications, funding, and research topics at scale.

## Node Types

### 1. Researcher
Represents an individual researcher in the NRG ecosystem.

**Properties:**
- `researcher_id` (UUID) - Unique identifier
- `name` (String) - Full name
- `email` (String) - Contact email
- `phone` (String) - Contact phone
- `orcid` (String) - ORCID identifier
- `state` (String) - Geographic state
- `research_area` (String) - Primary research area
- `year_joined` (Integer) - Year joined institution
- `created_at` (DateTime) - Record creation timestamp
- `updated_at` (DateTime) - Record update timestamp

### 2. Institution
Represents academic or research institutions.

**Properties:**
- `institution_id` (UUID) - Unique identifier
- `name` (String) - Institution name
- `type` (String) - Type: university, lab, company, etc.
- `state` (String) - Geographic state
- `country` (String) - Country code
- `founded_year` (Integer) - Year founded
- `website` (String) - Institution website
- `created_at` (DateTime) - Record creation timestamp
- `updated_at` (DateTime) - Record update timestamp

### 3. Publication
Represents academic publications, papers, and research outputs.

**Properties:**
- `publication_id` (UUID) - Unique identifier
- `title` (String) - Publication title
- `abstract` (String) - Abstract/description
- `venue` (String) - Journal/conference name
- `year` (Integer) - Publication year
- `doi` (String) - Digital Object Identifier
- `pmid` (String) - PubMed ID
- `created_at` (DateTime) - Record creation timestamp
- `updated_at` (DateTime) - Record update timestamp

### 4. Lab
Represents research laboratories or groups.

**Properties:**
- `lab_id` (UUID) - Unique identifier
- `name` (String) - Lab name
- `institution_id` (UUID) - Parent institution ID
- `research_area` (String) - Primary research area
- `established_year` (Integer) - Year established
- `website` (String) - Lab website
- `created_at` (DateTime) - Record creation timestamp
- `updated_at` (DateTime) - Record update timestamp

### 5. Funding
Represents funding grants and financial support.

**Properties:**
- `funding_id` (UUID) - Unique identifier
- `researcher_id` (UUID) - Principal investigator
- `institution_id` (UUID) - Administering institution
- `agency` (String) - Funding agency
- `amount` (Float) - Funding amount
- `start_date` (Date) - Funding start date
- `end_date` (Date) - Funding end date
- `title` (String) - Funding title
- `created_at` (DateTime) - Record creation timestamp
- `updated_at` (DateTime) - Record update timestamp

### 6. Venue
Represents publication venues (journals, conferences).

**Properties:**
- `name` (String) - Venue name
- `type` (String) - Type: journal, conference, workshop
- `impact_factor` (Float) - Journal impact factor
- `issn` (String) - ISSN identifier

### 7. Keyword
Represents research topics and keywords.

**Properties:**
- `keyword` (String) - Keyword text
- `category` (String) - Category: method, domain, technique, etc.
- `created_at` (DateTime) - Record creation timestamp

## Relationship Types

### 1. AFFILIATED_WITH (Researcher → Institution)
Represents researcher institutional affiliation.

**Properties:**
- `start_date` (Date) - Affiliation start date
- `end_date` (Date) - Affiliation end date
- `position` (String) - Position title
- `created_at` (DateTime) - Relationship creation timestamp

### 2. AUTHORED (Researcher → Publication)
Represents authorship relationships.

**Properties:**
- `author_order` (Integer) - Author order in publication
- `created_at` (DateTime) - Relationship creation timestamp

### 3. MEMBER_OF (Researcher → Lab)
Represents lab membership.

**Properties:**
- `start_date` (Date) - Membership start date
- `end_date` (Date) - Membership end date
- `role` (String) - Role: PI, postdoc, student, collaborator
- `created_at` (DateTime) - Relationship creation timestamp

### 4. COLLABORATES_WITH (Researcher ↔ Researcher)
Represents research collaborations.

**Properties:**
- `strength` (Float) - Collaboration strength (based on co-authorship count)
- `first_collab_year` (Integer) - First collaboration year
- `last_collab_year` (Integer) - Last collaboration year
- `created_at` (DateTime) - Relationship creation timestamp

### 5. LOCATED_AT (Lab → Institution)
Represents lab institutional location.

### 6. PUBLISHED_IN (Publication → Venue)
Represents publication venue relationship.

### 7. FUNDED_BY (Funding → Researcher)
Represents funding principal investigator relationship.

### 8. ADMINISTERED_BY (Funding → Institution)
Represents funding administration relationship.

### 9. MENTORED (Researcher → Researcher)
Represents mentorship relationships.

**Properties:**
- `start_date` (Date) - Mentorship start date
- `end_date` (Date) - Mentorship end date
- `created_at` (DateTime) - Relationship creation timestamp

### 10. COLLABORATES_WITH (Lab ↔ Lab)
Represents lab collaboration relationships.

**Properties:**
- `start_date` (Date) - Collaboration start date
- `end_date` (Date) - Collaboration end date
- `project_count` (Integer) - Number of joint projects
- `created_at` (DateTime) - Relationship creation timestamp

### 11. CITES (Publication → Publication)
Represents citation relationships.

### 12. INTERESTED_IN (Researcher → Keyword)
Represents researcher research interests.

**Properties:**
- `strength` (Float) - Interest strength (0.0-1.0)
- `created_at` (DateTime) - Relationship creation timestamp

### 13. HAS_KEYWORD (Publication → Keyword)
Represents publication topic keywords.

### 14. SPECIALIZES_IN (Lab → Keyword)
Represents lab research specializations.

### 15. FOCUSES_ON (Institution → Keyword)
Represents institutional research focus areas.

## Indexes and Constraints

### Constraints
- Unique constraints on all node ID properties
- Node property existence constraints where appropriate

### Indexes
- Researcher: state, research_area
- Institution: type
- Publication: year, venue
- Lab: research_area
- Funding: agency, start_date
- Keyword: keyword text

## Performance Considerations

### Scaling to 600GB Dataset
The knowledge graph design accounts for the full 600GB dataset through:

1. **Sharding Strategy**: Logical sharding by research area and institution
2. **Index Optimization**: Composite indexes for common query patterns
3. **Caching Layer**: Redis caching for frequently accessed nodes/relationships
4. **Query Optimization**: Parameterized queries with execution plan analysis
5. **Memory Management**: Configured Neo4j page cache for large dataset handling

## Security and Access Control

### RBAC Integration
The knowledge graph integrates with database-level RBAC through:
- Access tier metadata on all nodes and relationships
- Query filtering based on user access levels
- Audit logging for sensitive data access

## Traversal Patterns
The following common traversal patterns are implemented:

1. **Collaborator Discovery**: Find researchers with shared interests
2. **Topic Clustering**: Group researchers by research areas
3. **Funding Analysis**: Track funding sources and amounts
4. **Capability Mapping**: Identify expertise in specific technologies
5. **Institutional Overlap**: Find shared research areas between institutions

## Monitoring and Maintenance

### Performance Metrics
- Query execution time < 200ms for 95% of queries
- Memory utilization optimized for 128GB+ RAM systems
- Connection pooling for high-concurrency access

### Data Quality
- Automated validation of node and relationship integrity
- Regular consistency checks and repair procedures
- Backup and recovery procedures for large-scale operations

## Implementation Roadmap

### Phase 1: Core Schema Deployment
- Node and relationship schema definition
- Constraint and index creation
- Initial data loading procedures

### Phase 2: Performance Optimization
- Query optimization and caching implementation
- Sharding strategy deployment
- Monitoring and alerting setup

### Phase 3: Security Integration
- RBAC implementation and testing
- Audit logging and compliance verification
- Access control validation

This design enables sub-second query performance at the 600GB scale while maintaining data integrity and security compliance.