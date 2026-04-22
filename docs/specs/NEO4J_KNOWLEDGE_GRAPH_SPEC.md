# Feature Spec: Neo4j Knowledge Graph Integration
**Phase:** Phase 2 (Month 6–8, feature-flagged in Phase 1)
**Document Status:** Draft
**Author:** NRG Platform Team

---

## 1. Problem Statement

The current database stores relationships as foreign keys and junction tables, but:

1. **Multi-hop relationship queries are slow** — "Find researchers who co-authored with someone who worked at CCMB and received DST funding" requires multiple JOINs
2. **Collaboration networks are opaque** — It's hard to answer "who are the most influential collaborators in the network"
3. **Topic relationships are implicit** — Publications have keywords, but the relationships between research topics aren't surfaced
4. **GraphView frontend needs real graph data** — The Sigma.js GraphView exists but renders mock data

The knowledge graph makes relationship-first queries fast and enables graph algorithms (PageRank, community detection, path finding) that are impractical in SQL.

---

## 2. Goals

1. **Fast multi-hop queries** — 2–3 hop relationships in <100ms
2. **Graph algorithms** — PageRank for researcher influence, community detection for research clusters
3. **Interactive GraphView** — Real data in the frontend Sigma.js graph
4. **Path finding** — "Find the shortest path between Dr. Patel and Dr. Sharma through collaborations"

---

## 3. Non-Goals

- Replace the relational database — NRG's primary data store remains SQLite/PostgreSQL
- Real-time graph updates — graph is rebuilt from DB on a schedule (daily)
- Full-text search in Neo4j — use Qdrant for this
- Graph-based ranking as the primary ranking signal — SQL aggregation remains authoritative

---

## 4. Data Model

### 4.1 Node Types

```
(Researcher)
  - researcher_id: string (links to SQLite/PostgreSQL)
  - name: string
  - research_area: string
  - h_index: int
  - institution_id: string
  - tier_access: int

(Publication)
  - publication_id: string
  - title: string
  - year: int
  - access_tier: int

(Project)
  - project_id: string
  - title: string
  - funding_agency: string
  - status: string

(Institution)
  - institution_id: string
  - name: string
  - state: string
  - type: string ("IIT" | "NIT" | "CSIR" | "University" | "Other")

(Lab)
  - lab_id: string
  - name: string
  - institution_id: string
```

### 4.2 Relationship Types

```
(Researcher)-[:CO_AUTHORED_WITH {paper_ids: [], year: int}]->(Researcher)
(Researcher)-[:PUBLISHED]->(Publication)
(Researcher)-[:WORKING_AT {role: string}]->(Institution)
(Researcher)-[:AFFILIATED_WITH]->(Lab)
(Researcher)-[:FUNDED_BY]->(Project)
(Researcher)-[:COLLABORATES_WITH {project_id: string}]->(Researcher)
(Publication)-[:PUBLISHED_AT]->(Institution)
(Project)-[:FUNDED_BY {agency: string}]->(Institution)
(Lab)-[:PART_OF]->(Institution)
(Researcher)-[:HAS_EXPERTISE_IN {score: float}]->(Topic)  -- Topic as virtual node
```

### 4.3 Graph Schema

```cypher
// Create constraints
CREATE CONSTRAINT researcher_id IF NOT EXISTS
FOR (r:Researcher) REQUIRE r.researcher_id IS UNIQUE

CREATE CONSTRAINT publication_id IF NOT EXISTS
FOR (p:Publication) REQUIRE p.publication_id IS UNIQUE

CREATE CONSTRAINT institution_id IF NOT EXISTS
FOR (i:Institution) REQUIRE i.institution_id IS UNIQUE

CREATE CONSTRAINT project_id IF NOT EXISTS
FOR (p:Project) REQUIRE p.project_id IS UNIQUE

CREATE CONSTRAINT lab_id IF NOT EXISTS
FOR (l:Lab) REQUIRE l.lab_id IS UNIQUE
```

---

## 5. Architecture

```
┌─────────────────────┐
│  SQLite/PostgreSQL  │  Primary data store (source of truth)
└──────────┬──────────┘
           │ Nightly sync (or on-demand rebuild)
           ▼
┌─────────────────────┐
│   Neo4j Database     │  Graph store (relationship queries)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│  GraphService (src/services/graph/)     │
│  - query_graph()                        │
│  - find_paths()                         │
│  - get_influence_scores()               │
│  - detect_communities()                 │
└──────────┬──────────────────────────────┘
           │
    ┌──────┴──────┐
    ▼             ▼
/query/graph  GraphView
   API          Frontend
```

### 5.1 Sync Strategy

```
Nightly Job (cron):
  1. Export relationships from SQLite (COALESCE joins)
  2. Transform to Neo4j CSV format
  3. neo4j-admin bulk import (replaces graph)
  4. Verify node/edge counts match source
  5. Smoke test: run 5 critical queries
```

**Why replace, not update:**
- Neo4j bulk import is faster than incremental updates for large graphs
- Daily rebuilds are acceptable (not real-time)
- Simpler consistency story

### 5.2 GraphService API

```python
class GraphService:
    def query_graph(
        self,
        query: str,
        user_tier: int,
        max_hops: int = 3,
        limit: int = 50
    ) -> list[dict]:
        """
        Natural language graph query.
        Returns paths/nodes matching the relationship pattern.
        """

    def find_shortest_path(
        self,
        researcher_a: str,
        researcher_b: str,
        max_length: int = 4
    ) -> list[dict]:
        """
        Find shortest collaboration path between two researchers.
        """

    def get_researcher_influence(
        self,
        researcher_id: str,
        method: str = "pagerank"
    ) -> float:
        """
        Get influence score for a researcher.
        Methods: pagerank, citations, collaborations
        """

    def get_research_clusters(
        self,
        min_cluster_size: int = 5,
        algorithm: str = "louvain"
    ) -> list[dict]:
        """
        Detect research communities/clusters.
        """
```

---

## 6. Implementation Phases

### Phase 1: Graph Build + Basic Queries (Month 6)
- [ ] Set up Neo4j in docker-compose alongside existing services
- [ ] Build CSV exporter from SQLite relationships
- [ ] Import researchers, publications, institutions, labs, projects
- [ ] Import: CO_AUTHORED_WITH, PUBLISHED, WORKING_AT, AFFILIATED_WITH, FUNDED_BY
- [ ] Implement `query_graph()` — Cypher query execution
- [ ] Feature flag: `FEATURE_KG=false` (off by default)

### Phase 2: Graph Algorithms (Month 7)
- [ ] Implement PageRank for researcher influence
- [ ] Implement community detection (Louvain algorithm)
- [ ] Implement `get_researcher_influence()`
- [ ] Implement `get_research_clusters()`
- [ ] Add influence scores to researcher profiles

### Phase 3: Advanced Graph Queries (Month 8)
- [ ] Implement `find_shortest_path()` — collaboration path finding
- [ ] Implement `find_key_bridges()` — researchers who connect different communities
- [ ] Implement `get_research_trends()` — topic evolution over time
- [ ] Performance test: 90th percentile query < 100ms

### Phase 4: GraphView Frontend (Month 8)
- [ ] Wire GraphService to `/query/graph` API endpoint
- [ ] Update GraphView.tsx to use real graph data
- [ ] Add node click → researcher profile modal
- [ ] Add edge click → collaboration detail
- [ ] Tier filtering: Industry (Tier 3) sees anonymized nodes

---

## 7. Cypher Query Examples

### 7.1 Find Collaborators of a Researcher
```cypher
MATCH (r:Researcher {researcher_id: $id})-[:CO_AUTHORED_WITH]-(c:Researcher)
WHERE r.tier_access <= $user_tier
RETURN c.name, c.research_area, count(*) as collaborations
ORDER BY collaborations DESC
LIMIT 20
```

### 7.2 Find Shortest Path Between Two Researchers
```cypher
MATCH path = shortestPath(
  (a:Researcher {researcher_id: $id_a})-[*1..4]-(b:Researcher {researcher_id: $id_b})
)
WHERE all(r IN nodes(path) WHERE r.tier_access <= $user_tier)
RETURN path
```

### 7.3 Find Key Bridge Researchers (Between Communities)
```cypher
CALL algo.betweenness(
  'MATCH (r:Researcher) RETURN id(r) as id',
  'MATCH (r1:Researcher)-[:CO_AUTHORED_WITH]-(r2:Researcher) RETURN id(r1) as source, id(r2) as target',
  {graph:'cypher', writeProperty: 'betweenness'}
)
YIELD nodeId, score
RETURN researcher_id, score
ORDER BY score DESC
LIMIT 20
```

---

## 8. Tier Enforcement in Graph Queries

| Tier | What They See | Cypher Filter |
|------|--------------|---------------|
| 1 (Researcher) | Full names, all relationships | `WHERE r.tier_access <= 1` |
| 2 (Government) | Anonymized nodes (R001, R002), aggregate stats | No individual names |
| 3 (Industry) | Institution-level only, no individual researchers | `OPTIONAL MATCH` for anonymized |

**Tier 2 anonymization query:**
```cypher
MATCH (r:Researcher)
WHERE r.tier_access <= 2
RETURN 'R-' + substring(r.researcher_id, -4) as anon_id,
       r.research_area as area,
       size((r)-[:CO_AUTHORED_WITH]->()) as collab_count
```

---

## 9. Performance Requirements

| Metric | Target | Notes |
|--------|--------|-------|
| Graph build time (nightly) | < 30 min | For 5,615 researchers + 50K relationships |
| 2-hop query latency (p50) | < 50ms | Neo4j indexed query |
| 2-hop query latency (p90) | < 100ms | Neo4j indexed query |
| Path finding latency (p90) | < 500ms | BFS up to 4 hops |
| Graph rebuild frequency | Daily | Via cron job |

---

## 10. Dependencies

| Dependency | Owner | Blocker For |
|-----------|-------|-------------|
| Neo4j in docker-compose | Infra | All phases |
| CSV exporter from SQLite | Data Team | Phase 1 |
| Cypher query validation | AI Team | Phase 1 |
| Neo4j APOC library | Infra | Phase 2 (algorithms) |
| GraphService unit tests | QA | Phase 1 |
| Performance benchmarks | QA | Phase 3 |

---

## 11. Open Questions

1. **Ownership of graph sync** — Should the graph rebuild be a separate service or part of the existing data pipeline?
2. **Graph vs Qdrant for topic relationships** — Should topic similarity use Neo4j graph distances or Qdrant vector similarity?
3. **Real-time vs eventual consistency** — Daily rebuilds are acceptable for now, but when should this become real-time?
4. **Neo4j vs NetworkX for algorithms** — Should we run algorithms in Neo4j (via APOC/Alog plugin) or export to Python (NetworkX) for complex analysis?