-- Migration: Index optimization for performance
-- Description: Add additional indexes for query performance optimization

BEGIN;

-- Add composite indexes for common query patterns
-- Researchers table composite indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_researchers_institution_tier ON researchers(institution_id, access_tier);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_researchers_specialization_tier ON researchers(specialization, access_tier);

-- Labs table composite indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_labs_institution_tier ON labs(institution_id, access_tier);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_labs_area_tier ON labs(research_area, access_tier);

-- Publications table composite indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_publications_year_tier ON publications(year, access_tier);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_publications_citation_count ON publications(citation_count DESC);

-- Institutions table composite indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_institutions_state_type ON institutions(state, type);

-- Funding table composite indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_funding_agency_status ON funding(agency, status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_funding_pi_status ON funding(principal_investigator_id, status);

-- Users table composite indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_role_tier ON users(role, access_tier);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_active ON users(is_active);

-- Vector metadata table indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_vector_metadata_collection_institution ON vector_metadata(collection_name, institution);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_vector_metadata_access_institution ON vector_metadata(access_tier, institution);

-- Add partial indexes for filtered queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_researchers_active ON researchers((1)) WHERE access_tier = '1';
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_labs_active ON labs((1)) WHERE access_tier = '1';
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_publications_active ON publications((1)) WHERE access_tier = '1';

-- Add expression indexes for text search
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_researchers_name_trgm ON researchers USING gin(last_name gin_trgm_ops);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_researchers_first_name_trgm ON researchers USING gin(first_name gin_trgm_ops);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_institutions_name_trgm ON institutions USING gin(name gin_trgm_ops);

-- Add indexes for date range queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_publications_year_range ON publications(year);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_researchers_created_at ON researchers(created_at);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_labs_created_at ON labs(created_at);

-- Add indexes for JSONB search
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_researchers_privacy_settings ON researchers USING gin(privacy_settings);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_privacy_settings ON users USING gin(privacy_settings);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_publications_topics ON publication_topics USING gin(topic_id);

-- Add indexes for API usage tracking
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_api_usage_time_method ON api_usage(request_time, method);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_api_usage_endpoint_status ON api_usage(endpoint, status_code);

-- Add indexes for audit logging
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_log_time_action ON audit_log(created_at, action);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_log_user_time ON audit_log(user_id, created_at);

COMMIT;