# NRG Entity Definitions and Relationships

## Core Entities

### Researcher
- **Definition**: An individual researcher, scientist, or academic affiliated with an Indian institution
- **Primary Table**: `researchers`
- **ID Field**: `researcher_id` (UUID)
- **Business Key**: `orcid` (when available), otherwise `email`
- **Relationships**:
  - → `institutions` (implicit via `state` or `research_area`, NOT a direct FK)
  - → `funding` (1:many via `researcher_id`)
  - → `labs` (implicit; no direct FK)
  - → `publications` (NO direct FK; linkage via ORCID or name matching)
- **Common Filters**: `access_tier <= :user_tier`; exclude `name ILIKE '%test%'`

### Institution
- **Definition**: A university, college, research center, or academic organization in India
- **Primary Table**: `institutions`
- **ID Field**: `institution_id` (UUID)
- **Business Key**: `name` (unique but not enforced at DB level)
- **Relationships**:
  - → `researchers` (implicit via `state`)
  - → `funding` (1:many via `institution_id`)
  - → `labs` (1:many via `institution_id`)
- **Common Filters**: `country = 'India'` (should always be true); `type IN ('University', 'IIT', 'NIT', 'Research Institute')`

### Publication
- **Definition**: A research paper, article, or scholarly work
- **Primary Table**: `publications`
- **ID Field**: `publication_id` (UUID)
- **Business Key**: `doi` (when available), otherwise `title` + `year`
- **Relationships**:
  - → `researchers` (NO direct FK; linkage via ORCID or text search)
  - → `keywords` (NO direct FK; keyword extraction from title/abstract)
- **Common Filters**: `doi IS NOT NULL` (exclude preprints); `year >= 2015` (recent research)

### Lab
- **Definition**: A research laboratory or group within an institution
- **Primary Table**: `labs`
- **ID Field**: `lab_id` (UUID)
- **Relationships**:
  - → `institutions` (many:1 via `institution_id`)
  - → `researchers` (implicit via `research_area`)
- **Common Filters**: `established_year >= 2000` (active labs)

### Funding
- **Definition**: A grant, award, or financial support for research
- **Primary Table**: `funding`
- **ID Field**: `funding_id` (UUID)
- **Relationships**:
  - → `researchers` (many:1 via `researcher_id`)
  - → `institutions` (many:1 via `institution_id`)
- **Common Filters**: `amount IS NOT NULL`; `start_date <= CURRENT_DATE`

---

## Academic Schema Entities

### Government Grant
- **Definition**: Funding received from a government organization under a specific scheme
- **Primary Table**: `innovation_grant_from_govt`
- **ID Field**: `id` (TEXT, NOT UUID)
- **Key Difference**: Uses `institute` (TEXT name) instead of `institution_id` (UUID)
- **Relationships**: → `institutions` (by name matching, NOT FK)

### Patent
- **Definition**: An Indian Patent Office (IPO) patent application or grant
- **Primary Table**: `combined_ipo_patent_data`
- **ID Field**: `id` (TEXT)
- **Business Key**: `application_number`
- **Status Values**: 'Granted', 'Filed', 'Examined', 'Rejected'
- **Key Difference**: Uses `institute` (TEXT) and `applicants` (TEXT), not UUIDs

### TRL Innovation
- **Definition**: An innovation tracked through Technology Readiness Levels
- **Primary Table**: `innovations_at_various_stages_of_technology_readiness_level`
- **ID Field**: `id` (TEXT)
- **TRL Scale**: 1-9 (1=Basic research, 9=Commercial deployment)

### Student
- **Definition**: A student enrolled in a program at an institution
- **Spread Across**: `phd_students`, `sanctioned_intake`, `actual_student_strength`
- **Key Difference**: `sanctioned_intake` = approved capacity; `actual_student_strength` = enrolled count

---

## Entity Relationship Diagram (Simplified)

```
[institutions] ──1:N──→ [labs]
    │   │
    │   └──1:N──→ [funding]
    │
    └──implicit──→ [researchers] (via state/research_area)

[researchers] ──1:N──→ [funding]
    │
    └──NO FK──→ [publications] (link via ORCID or text)

[academic schema tables] ──text match──→ [institutions] (via name, NOT FK)
```

## Key Join Paths

### Core Schema Joins
```sql
-- Researchers + their institutions (via state approximation)
SELECT r.*, i.name AS institution_name
FROM researchers r
LEFT JOIN institutions i ON r.state = i.state  -- APPROXIMATE
WHERE i.type = 'IIT';  -- Narrow down if needed

-- Researchers + their funding
SELECT r.name, f.agency, f.amount
FROM researchers r
JOIN funding f ON r.researcher_id = f.researcher_id;

-- Institutions + their labs
SELECT i.name, COUNT(l.lab_id) AS lab_count
FROM institutions i
LEFT JOIN labs l ON i.institution_id = l.institution_id
GROUP BY i.institution_id, i.name;
```

### Academic Schema Joins
```sql
-- Grants + institution details (via name matching)
SELECT g.*, i.type, i.founded_year
FROM innovation_grant_from_govt g
LEFT JOIN institutions i ON g.institute = i.name;

-- Patents + institution
SELECT p.*, i.state
FROM combined_ipo_patent_data p
LEFT JOIN institutions i ON p.institute = i.name;
```

### Cross-Schema Joins (Advanced)
```sql
-- Funding from BOTH core + academic schema
WITH core_funding AS (
    SELECT i.name AS institute, SUM(f.amount) AS core_amount
    FROM funding f
    JOIN institutions i ON f.institution_id = i.institution_id
    GROUP BY i.name
),
academic_grants AS (
    SELECT institute, SUM(grant_received) AS academic_amount
    FROM innovation_grant_from_govt
    GROUP BY institute
)
SELECT 
    COALESCE(c.institute, a.institute) AS institute,
    COALESCE(c.core_amount, 0) AS core_funding,
    COALESCE(a.academic_amount, 0) AS academic_funding,
    COALESCE(c.core_amount, 0) + COALESCE(a.academic_amount, 0) AS total_funding
FROM core_funding c
FULL OUTER JOIN academic_grants a ON c.institute = a.institute;
```
