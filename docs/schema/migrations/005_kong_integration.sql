-- Migration: Kong API Gateway Integration
-- Description: Add database structures for Kong API gateway integration

BEGIN;

-- Create table for API keys and access management
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(user_id),
    api_key VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100),
    description TEXT,
    permissions JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE
);

-- Create indexes for API keys
CREATE INDEX IF NOT EXISTS idx_api_keys_user ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_key ON api_keys(api_key);
CREATE INDEX IF NOT EXISTS idx_api_keys_active ON api_keys(is_active);

-- Create table for API usage tracking
CREATE TABLE IF NOT EXISTS api_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    api_key_id UUID REFERENCES api_keys(id),
    endpoint VARCHAR(255),
    method VARCHAR(10),
    ip_address INET,
    user_agent TEXT,
    request_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    response_time INTEGER, -- in milliseconds
    status_code INTEGER,
    data_size BIGINT
);

-- Create indexes for API usage
CREATE INDEX IF NOT EXISTS idx_api_usage_key ON api_usage(api_key_id);
CREATE INDEX IF NOT EXISTS idx_api_usage_endpoint ON api_usage(endpoint);
CREATE INDEX IF NOT EXISTS idx_api_usage_time ON api_usage(request_time);

-- Create table for rate limiting configuration
CREATE TABLE IF NOT EXISTS rate_limits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(user_id),
    api_key_id UUID REFERENCES api_keys(id),
    limit_type VARCHAR(50), -- 'rpm', 'rph', 'rpd' (requests per minute/hour/day)
    limit_value INTEGER,
    window_start TIMESTAMP WITH TIME ZONE,
    window_end TIMESTAMP WITH TIME ZONE,
    request_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for rate limits
CREATE INDEX IF NOT EXISTS idx_rate_limits_user ON rate_limits(user_id);
CREATE INDEX IF NOT EXISTS idx_rate_limits_key ON rate_limits(api_key_id);
CREATE INDEX IF NOT EXISTS idx_rate_limits_window ON rate_limits(window_start, window_end);

-- Add API key reference to users table
ALTER TABLE users
ADD COLUMN IF NOT EXISTS default_api_key UUID REFERENCES api_keys(id);

-- Create view for API access monitoring
CREATE OR REPLACE VIEW v_api_access_monitor AS
SELECT 
    u.name as user_name,
    u.role as user_role,
    ak.name as api_key_name,
    au.endpoint,
    au.method,
    au.request_time,
    au.response_time,
    au.status_code,
    au.data_size
FROM api_usage au
JOIN api_keys ak ON au.api_key_id = ak.id
JOIN users u ON ak.user_id = u.user_id
ORDER BY au.request_time DESC;

-- Create function to check API key validity
CREATE OR REPLACE FUNCTION check_api_key_validity(api_key_text VARCHAR(255))
RETURNS TABLE(
    is_valid BOOLEAN,
    user_id UUID,
    permissions JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ak.is_active AND (ak.expires_at IS NULL OR ak.expires_at > NOW()),
        ak.user_id,
        ak.permissions
    FROM api_keys ak
    WHERE ak.api_key = api_key_text;
END;
$$ LANGUAGE plpgsql;

-- Create function to log API usage
CREATE OR REPLACE FUNCTION log_api_usage(
    api_key_id UUID,
    endpoint VARCHAR(255),
    method VARCHAR(10),
    ip INET,
    user_agent TEXT,
    response_time INTEGER,
    status_code INTEGER,
    data_size BIGINT
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO api_usage (
        api_key_id, endpoint, method, ip_address, user_agent,
        response_time, status_code, data_size
    ) VALUES (
        api_key_id, endpoint, method, ip, user_agent,
        response_time, status_code, data_size
    );
END;
$$ LANGUAGE plpgsql;

-- Create function to check rate limits
CREATE OR REPLACE FUNCTION check_rate_limit(
    user_id UUID,
    api_key_id UUID,
    limit_type VARCHAR(50),
    limit_value INTEGER
)
RETURNS BOOLEAN AS $$
DECLARE
    current_count INTEGER;
BEGIN
    -- Get current request count for the user/key in the current window
    SELECT COALESCE(SUM(request_count), 0) INTO current_count
    FROM rate_limits rl
    WHERE rl.user_id = check_rate_limit.user_id
    AND rl.api_key_id = check_rate_limit.api_key_id
    AND rl.limit_type = check_rate_limit.limit_type
    AND rl.window_end > NOW();
    
    -- Return true if limit exceeded, false otherwise
    RETURN current_count >= limit_value;
END;
$$ LANGUAGE plpgsql;

-- Add comments for API integration tables
COMMENT ON TABLE api_keys IS 'Table for API key management and access control for Kong integration';
COMMENT ON TABLE api_usage IS 'Table for tracking API usage for monitoring and analytics';
COMMENT ON TABLE rate_limits IS 'Table for API rate limiting configuration and tracking';

COMMIT;