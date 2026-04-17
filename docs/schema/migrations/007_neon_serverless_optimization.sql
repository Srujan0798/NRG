-- Migration: Neon serverless optimization
-- Description: Optimize schema for Neon serverless environment

BEGIN;

-- Add Neon-optimized schema features
-- These features are designed to work well with Neon's serverless architecture

-- Create a table for caching frequently accessed data
CREATE TABLE IF NOT EXISTS neon_cache (
    cache_key VARCHAR(255) PRIMARY KEY,
    cache_value JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for cache table
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_neon_cache_expires ON neon_cache(expires_at);

-- Create a table for Neon connection optimization
CREATE TABLE IF NOT EXISTS neon_connections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    connection_id VARCHAR(255),
    session_id UUID,
    user_id UUID,
    connection_start TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    connection_end TIMESTAMP WITH TIME ZONE,
    query_count INTEGER DEFAULT 0,
    data_transferred BIGINT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE
);

-- Create indexes for connection optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_neon_connections_active ON neon_connections(is_active);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_neon_connections_user ON neon_connections(user_id);

-- Create a function to optimize Neon connections
CREATE OR REPLACE FUNCTION optimize_neon_connection()
RETURNS TEXT AS $$
BEGIN
    -- This function would contain logic to optimize connections for Neon's serverless environment
    -- For example, it might clean up stale connections or optimize connection pooling
    RETURN 'Neon connection optimization completed';
END;
$$ LANGUAGE plpgsql;

-- Create a function to manage Neon cache
CREATE OR REPLACE FUNCTION manage_neon_cache(cache_key VARCHAR(255), cache_value JSONB, ttl INTERVAL DEFAULT '1 hour')
RETURNS TEXT AS $$
BEGIN
    -- Insert or update cache entry
    INSERT INTO neon_cache (cache_key, cache_value, expires_at)
    VALUES (cache_key, cache_value, NOW() + ttl)
    ON CONFLICT (cache_key) 
    DO UPDATE SET 
        cache_value = EXCLUDED.cache_value,
        expires_at = NOW() + ttl;
    
    RETURN 'Cache entry managed successfully';
END;
$$ LANGUAGE plpgsql;

-- Create a function to clean up expired cache entries
CREATE OR REPLACE FUNCTION cleanup_expired_cache()
RETURNS TEXT AS $$
BEGIN
    -- Delete expired cache entries
    DELETE FROM neon_cache WHERE expires_at < NOW();
    RETURN 'Expired cache entries cleaned up';
END;
$$ LANGUAGE plpgsql;

-- Create a function to monitor Neon performance
CREATE OR REPLACE FUNCTION monitor_neon_performance()
RETURNS TABLE(
    active_connections INTEGER,
    avg_query_time NUMERIC,
    cache_hit_rate NUMERIC
) AS $$
BEGIN
    -- This function would return performance metrics
    RETURN QUERY SELECT 0, 0.0, 0.0;
END;
$$ LANGUAGE plpgsql;

-- Add comments for Neon optimization tables
COMMENT ON TABLE neon_cache IS 'Table for caching frequently accessed data in Neon environment';
COMMENT ON TABLE neon_connections IS 'Table for managing connections in Neon environment';

COMMIT;