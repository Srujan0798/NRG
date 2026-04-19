# NRG Knowledge Graph Specification v1.0

**Status**: Historical/Phase 2 design note. Phase 1 uses the DB-backed `/query/graph` endpoint. Neo4j code is quarantined under `experiments/knowledge_graph/` and is not part of the current working platform unless explicitly promoted and tested.

## Neo4j Graph Model

Aligned with future/experimental Neo4j work, not current `src` runtime code.

### Node Types

| Node | Properties | Constraints |
|------|------------|-------------|
| `Researcher` | researcher_id, name, email, phone, ORCID, state, research_area, year_joined | researcher_id UNIQUE |
| `Institution` | institution_id, name, type, state, country, founded_year, website | institution_id UNIQUE |
| `Publication` | publication_id, title, abstract, venue, year, DOI, PMID | publication_id UNIQUE |
| `Lab` | lab_id, name, institution_id, research_area, established_year, website | lab_id UNIQUE |
| `Funding` | funding_id, researcher_id, institution_id, agency, amount, start_date, end_date, title | funding_id UNIQUE |
| `Venue` | name, type, impact_factor, ISSN | name UNIQUE |
| `Keyword` | keyword, category | keyword UNIQUE |

### Edge Types

| From | Relationship | To | Properties |
|------|--------------|------|------------|
| `Researcher` | `:AFFILIATED_WITH` | `Institution` | start_date, end_date, position |
| `Researcher` | `:AUTHORED` | `Publication` | author_order |
| `Researcher` | `:MEMBER_OF` | `Lab` | start_date, end_date, role |
| `Researcher` | `:COLLABORATES_WITH` | `Researcher` | strength, first_collab_year, last_collab_year |
| `Researcher` | `:MENTORED` | `Researcher` | start_date, end_date |
| `Researcher` | `:INTERESTED_IN` | `Keyword` | strength |
| `Lab` | `:LOCATED_AT` | `Institution` | - |
| `Lab` | `:COLLABORATES_WITH` | `Lab` | start_date, end_date, project_count |
| `Lab` | `:SPECIALIZES_IN` | `Keyword` | - |
| `Publication` | `:PUBLISHED_IN` | `Venue` | - |
| `Publication` | `:CITES` | `Publication` | - |
| `Publication` | `:HAS_KEYWORD` | `Keyword` | - |
| `Funding` | `:FUNDED_BY` | `Researcher` | - |
| `Funding` | `:ADMINISTERED_BY` | `Institution` | - |
| `Institution` | `:FOCUSES_ON` | `Keyword` | - |

### Cypher DDL

```cypher
-- Constraints (run first)
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

-- Indexes (for query performance)
CREATE INDEX researcher_state IF NOT EXISTS
FOR (r:Researcher) ON (r.state);

CREATE INDEX researcher_research_area IF NOT EXISTS
FOR (r:Researcher) ON (r.research_area);

CREATE INDEX publication_year IF NOT EXISTS
FOR (p:Publication) ON (p.year);

CREATE INDEX funding_agency IF NOT EXISTS
FOR (f:Funding) ON (f.agency);

-- Composite Indexes
CREATE INDEX researcher_institution_state IF NOT EXISTS
FOR (r:Researcher) ON (r.state, r.research_area);

CREATE INDEX publication_year_venue IF NOT EXISTS
FOR (p:Publication) ON (p.year, p.venue);
```

### Sample Queries

```cypher
-- Find collaborators of researcher
MATCH (r:Researcher {researcher_id: $id})-[:COLLABORATES_WITH]-(collab)
RETURN collab.name, collab.research_area;

-- Find publications by institution
MATCH (r:Researcher)-[:AFFILIATED_WITH]-(i:Institution {institution_id: $inst_id})
MATCH (r)-[:AUTHORED]-(p:Publication)
RETURN p.title, p.year, p.venue ORDER BY p.year DESC;

-- Find funding trends by state
MATCH (f:Funding)-[:FUNDED_BY]-(r:Researcher)-[:AFFILIATED_WITH]-(i:Institution)
WHERE i.state = $state
RETURN f.agency, SUM(f.amount) AS total_funding
ORDER BY total_funding DESC;
```

### Graph-to-Postgres Mapping

| Neo4j Node | Postgres Table | Sync Strategy |
|------------|--------------|-------------|
| Researcher | researchers |实时 |
| Institution | institutions |实时 |
| Publication | publications |实时 |
| Lab | labs |实时 |
| Funding | funding |实时 |
| Keyword | keywords |批量 |

---

*Historical design note. Current canonical architecture: `docs/architecture/ARCHITECTURE.md`.*
