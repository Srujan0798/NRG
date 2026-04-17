-- Index optimization script for National Research Graph database

BEGIN;

-- Researchers table indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_researchers_access_tier ON researchers(access_tier);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_researchers_institution ON researchers(institution_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_researchers_specialization ON researchers(specialization);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_researchers_name ON researchers(last_name, first_name);

-- Labs table indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_labs_access_tier ON labs(access_tier);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_labs_institution ON labs(institution_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_labs_area ON labs(research_area);

-- Publications table indexes
CREATE INDEX CONCURRENTLY IF NOT idx_publications_year ON publications(year);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_publications_doi ON publications(doi);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_publications_access_tier ON publications(access_tier);

-- Institutions table indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_institutions_state ON institutions(state);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_institutions_type ON institutions(type);

-- Funding table indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_funding_pi ON funding(principal_investigator_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_funding_agency ON funding(agency);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_funding_status ON funding(status);

-- Users table indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_tier ON users(access_tier);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_active ON users(is_active);

-- Topics table indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_topics_parent ON topics(parent_topic_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_topics_level ON topics(level);

-- Vector metadata indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_vector_metadata_collection ON vector_metadata(collection_name);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_vector_metadata_access ON vector_metadata(access_tier);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_vector_metadata_institution ON vector_metadata(institution);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_vector_metadata_topics ON vector_metadata USING GIN(topics);

-- Audit log indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_log_user ON audit_log(user_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_log_action ON audit_log(action);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_log_resource ON audit_log(resource_type, resource_id);

-- API keys indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_api_keys_user ON api_keys(user_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_api_keys_key ON api_keys(api_key);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_api_keys_active ON api_keys(is_active);

-- API usage indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_api_usage_key ON api_usage(api_key_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_api_usage_endpoint ON api_usage(endpoint);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_api_usage_time ON api_usage(request_time);

-- Rate limits indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_rate_limits_user ON rate_limits(user_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_rate_limits_key ON rate_limits(api_key_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_rate_limits_window ON rate_limits(window_start, window_end);

COMMIT;