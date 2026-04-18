# NRG RBAC Policy Specification v1.0

## Role Definitions

| Tier | Role | Description |
|------|------|-------------|
| 1 | Researcher | Full access to all data |
| 2 | Government | Aggregated/summary access only |
| 3 | Industry | Limited to public metadata only |

## Access Matrix (YAML)

```yaml
# docs/architecture/RBAC_POLICY.yaml

roles:
  researcher:
    tier: 1
    description: "Full access - internal researchers"
    tables:
      researchers:
        columns: ["*"]
        row_filter: "access_tier >= 1"
      institutions:
        columns: ["*"]
        row_filter: "access_tier >= 1"
      publications:
        columns: ["*"]
        row_filter: "access_tier >= 1"
      labs:
        columns: ["*"]
        row_filter: "access_tier >= 1"
      funding:
        columns: ["*"]
        row_filter: "access_tier >= 1"
      collaborations:
        columns: ["*"]
        row_filter: null
      keywords:
        columns: ["*"]
        row_filter: null
      researcher_keywords:
        columns: ["*"]
        row_filter: null
      audit_log:
        columns: ["*"]
        row_filter: null
      qdrant:
        collections:
          - "research_documents"
          - "researcher_profiles"
        filters:
          access_tier: ">= 1"
    query_limits:
      max_rows_per_query: 1000
      max_queries_per_minute: 100

  government:
    tier: 2
    description: "Aggregated summary access - policymakers"
    tables:
      researchers:
        columns: ["name", "research_area", "state", "year_joined"]
        row_filter: "access_tier >= 2"
        aggregation: true
      institutions:
        columns: ["name", "type", "state", "founded_year"]
        row_filter: "access_tier >= 2"
      publications:
        columns: ["title", "venue", "year", "doi"]
        row_filter: "access_tier >= 2"
      labs:
        columns: ["name", "research_area", "established_year"]
        row_filter: "access_tier >= 2"
      funding:
        columns: ["agency", "amount", "start_date", "end_date", "title"]
        row_filter: "access_tier >= 2"
        aggregation: true
      collaborations:
        columns: ["researcher_id_1", "researcher_id_2", "strength"]
        row_filter: null
      keywords:
        columns: ["keyword", "category"]
        row_filter: null
      qdrant:
        collections:
          - "research_documents"
          - "researcher_profiles"
        filters:
          access_tier: ">= 2"
    query_limits:
      max_rows_per_query: 100
      max_queries_per_minute: 50

  industry:
    tier: 3
    description: "Public metadata only - external partners"
    tables:
      researchers:
        columns: ["name", "research_area", "state"]
        row_filter: "access_tier = 3"
      institutions:
        columns: ["name", "type", "state"]
        row_filter: "access_tier = 3"
      publications:
        columns: ["title", "venue", "year"]
        row_filter: "access_tier = 3"
      labs:
        columns: ["name", "research_area"]
        row_filter: "access_tier = 3"
      funding:
        columns: ["agency", "title"]
        row_filter: "access_tier = 3"
        aggregation: true
      keywords:
        columns: ["keyword"]
        row_filter: null
      qdrant:
        collections:
          - "research_documents"
        filters:
          access_tier: 3
    query_limits:
      max_rows_per_query: 20
      max_queries_per_minute: 20

# Column Allowlists Per Table
column_allowlists:
  researchers:
    tier_1: ["*"]
    tier_2: ["name", "research_area", "state", "year_joined", "institution"]
    tier_3: ["name", "research_area", "state"]

  institutions:
    tier_1: ["*"]
    tier_2: ["name", "type", "state", "founded_year", "website"]
    tier_3: ["name", "type", "state"]

  publications:
    tier_1: ["*"]
    tier_2: ["title", "venue", "year", "doi"]
    tier_3: ["title", "venue", "year"]

  labs:
    tier_1: ["*"]
    tier_2: ["name", "research_area", "established_year"]
    tier_3: ["name", "research_area"]

  funding:
    tier_1: ["*"]
    tier_2: ["agency", "amount", "start_date", "end_date", "title"]
    tier_3: ["agency", "title"]
```

## Postgres RLS Policy DDL

```sql
-- RLS Policies (auto-generated from matrix)
CREATE POLICY researcher_select ON researchers
    FOR SELECT USING (
        CASE 
            WHEN current_setting('app.user_tier', true) = '1' THEN true
            WHEN current_setting('app.user_tier', true) = '2' THEN access_tier >= 2
            ELSE access_tier = 3
        END
    );

CREATE POLICY researcher_update ON researchers
    FOR UPDATE USING (current_setting('app.user_tier', true) = '1');

CREATE POLICY researcher_insert ON researchers
    FOR INSERT WITH CHECK (current_setting('app.user_tier', true) = '1');

CREATE POLICY researcher_delete ON researchers
    FOR DELETE USING (current_setting('app.user_tier', true) = '1');

-- Similar for other tables...
```

## Qdrant RBAC Filter

```python
# Qdrant payload filter per role
RESEARCHER_FILTER = {
    "must": [
        {"key": "access_tier", "range": {"gte": 1}}
    ]
}

GOVERNMENT_FILTER = {
    "must": [
        {"key": "access_tier", "range": {"gte": 2}}
    ]
}

INDUSTRY_FILTER = {
    "must": [
        {"key": "access_tier", "range": {"gte": 3}}
    ]
}
```

## Enforcement Points

| Layer | Implementation |
|-------|---------------|
| API Gateway | Kong plugin - role from JWT |
| Orchestration | LangGraph state - user_tier injection |
| Database | Postgres RLS policies |
| Vector DB | Qdrant payload filter |

---

*From this doc, you can write: CREATE TABLE, CREATE POLICY, Qdrant filter*