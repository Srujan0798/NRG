# ADR-002: Security Decisions

## Status
**Accepted** - Phase 1

## Context
Design security controls for the National Research Graph to ensure zero data leakage while enabling AI-assisted research queries.

## Decision

### 1. Zero-Egress Data Policy
- All research data remains in local PostgreSQL and Qdrant
- External LLMs receive only schema metadata and retrieved result IDs
- No raw documents or full records transmitted

### 2. Read-Only Sandbox
- Dedicated `nrg_readonly` PostgreSQL role
- SELECT-only grants enforced at database level
- INSERT/UPDATE/DDELETE blocked at connection level

### 3. Tier-Based Access Control
- Three-tier system mapped to access_tier ENUM
- PostgreSQL views filter by tier
- Qdrant metadata filtering by access_tier field

### 4. Audit Trail
- JSONL audit log in `.protocol/` directory
- Every query logged with user_tier, query_id, timestamp
- Immutable append-only logging

### 5. Prompt Injection Protection
- Schema-focused instructions to LLM
- No system prompt in user-visible data
- SQL injection blocked by sandbox

## Consequences

### Positive
- Verified zero data leakage
- Complete audit trail
- Enforced RBAC

### Negative
- Additional complexity in skill execution
- Requires separate read-only credentials

## Alternatives Considered

### Full RLS Implementation
- Deferred to Phase 2 for PostgreSQL 15+ requirement

### Local LLM Only
- Deferred - costly for Phase 1 PoC

## References
- STRIDE threat modeling
- OWASP Top 10
- Zero trust architecture