# ADR-001: Schema Design Decisions

## Status
**Accepted** - Phase 1

## Context
We need to design a relational schema for 600GB research dataset that supports:
- Multi-entity queries (researchers, labs, publications, funding, collaborations)
- Role-based access control at row level
- Integration with Qdrant vector database
- Read-only sandbox for LLM queries

## Decision

### 1. Normalization: 3NF
- All tables in Third Normal Form to minimize redundancy
- Proper foreign key constraints between entities
- UUID primary keys for distributed generation

### 2. Access Control via Enum Type
- Using PostgreSQL ENUM type `access_tier` for tiered access
- Values: '1' (researcher), '2' (government), '3' (industry)
- Applied at INSERT time, enforced via views and RLS

### 3. Many-to-Many Relationships
- Separate junction tables for researcher_lab, publication_author relationships
- Additional metadata (role, join_date, author_order) in junction tables
- Foreign key constraints with CASCADE delete

### 4. JSONB for Flexible Data
- Use JSONB for co_investigators array in funding table
- Enables flexible schema evolution
- Supports array indexing via GIN

### 5. Vector Metadata Side Table
- Separate `vector_metadata` table in PostgreSQL
- Links Qdrant point IDs to PostgreSQL records
- Stores access_tier, topics, institution for filtering

### 6. Read-Only Sandbox Role
- Dedicated `nrg_readonly` role with SELECT-only grants
- All LLM queries execute through this role
- Prevents accidental data modification

## Consequences

### Positive
- Clean data model reduces anomalies
- Enforced referential integrity
- RBAC at database level
- Audit trail via dedicated log table

### Negative
- Complex joins for multi-entity queries
- Additional migration complexity
- Requires understanding of ENUM types

## Alternatives Considered

### 1NF with application-level enforcement
- Rejected: No database-level guarantees

### Full Denormalization
- Deferred to Phase 2 for performance optimization

### Row-Level Security (RLS)
- Deferred: Requires PostgreSQL 15+ features
- Consider in Phase 2

## References
- PostgreSQL Documentation: ENUM types
- Database Normal Forms: Codd's 3NF
- Qdrant: Payload schema requirements