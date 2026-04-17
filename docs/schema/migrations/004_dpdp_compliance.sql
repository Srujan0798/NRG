-- Migration: Data Privacy and DPDP compliance
-- Description: Add data privacy and compliance features to database schema

BEGIN;

-- Add data privacy columns to all tables
-- These columns help with compliance with DPDP requirements

-- Add privacy columns to researchers table
ALTER TABLE researchers
ADD COLUMN IF NOT EXISTS consent_given BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS consent_date TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS data_retention_date TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS privacy_settings JSONB DEFAULT '{}';

-- Add privacy columns to users table
ALTER TABLE users
ADD COLUMN IF NOT EXISTS consent_given BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS consent_date TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS data_retention_date TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS privacy_settings JSONB DEFAULT '{}';

-- Add privacy columns to institutions table
ALTER TABLE institutions
ADD COLUMN IF NOT EXISTS privacy_settings JSONB DEFAULT '{}';

-- Add privacy columns to publications table
ALTER TABLE publications
ADD COLUMN IF NOT EXISTS privacy_settings JSONB DEFAULT '{}';

-- Add privacy columns to funding table
ALTER TABLE funding
ADD COLUMN IF NOT EXISTS privacy_settings JSONB DEFAULT '{}';

-- Create indexes for privacy columns
CREATE INDEX IF NOT EXISTS idx_researchers_consent ON researchers(consent_given, consent_date);
CREATE INDEX IF NOT EXISTS idx_users_consent ON users(consent_given, consent_date);
CREATE INDEX IF NOT EXISTS idx_researchers_retention ON researchers(data_retention_date);
CREATE INDEX IF NOT EXISTS idx_users_retention ON users(data_retention_date);

-- Create a view for data privacy compliance monitoring
CREATE OR REPLACE VIEW v_privacy_compliance AS
SELECT 
    'researchers' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN consent_given = TRUE THEN 1 END) as consent_given_count,
    COUNT(CASE WHEN consent_given = FALSE THEN 1 END) as consent_not_given_count,
    COUNT(CASE WHEN data_retention_date < NOW() THEN 1 END) as expired_data_count
FROM researchers
UNION ALL
SELECT 
    'users' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN consent_given = TRUE THEN 1 END) as consent_given_count,
    COUNT(CASE WHEN consent_given = FALSE THEN 1 END) as consent_not_given_count,
    COUNT(CASE WHEN data_retention_date < NOW() THEN 1 END) as expired_data_count
FROM users;

-- Create a function to check data retention compliance
CREATE OR REPLACE FUNCTION check_data_retention_compliance()
RETURNS TABLE(
    table_name TEXT,
    expired_records BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        'researchers' as table_name,
        COUNT(*) as expired_records
    FROM researchers 
    WHERE data_retention_date < NOW() AND consent_given = FALSE
    UNION ALL
    SELECT 
        'users' as table_name,
        COUNT(*) as expired_records
    FROM users 
    WHERE data_retention_date < NOW() AND consent_given = FALSE;
END;
$$ LANGUAGE plpgsql;

-- Create a function to anonymize user data
CREATE OR REPLACE FUNCTION anonymize_user_data(user_email TEXT)
RETURNS TEXT AS $$
BEGIN
    -- This function would implement data anonymization
    -- For compliance purposes
    UPDATE researchers 
    SET 
        first_name = 'Anonymous',
        last_name = 'User',
        email = 'anonymous@domain.com',
        phone = NULL,
        orcid = NULL,
        scopus_id = NULL,
        google_scholar_id = NULL,
        privacy_settings = jsonb_set(privacy_settings, '{anonymized}', 'true')
    WHERE email = user_email;
    
    UPDATE users 
    SET 
        name = 'Anonymous User',
        email = 'anonymous@domain.com',
        privacy_settings = jsonb_set(privacy_settings, '{anonymized}', 'true')
    WHERE email = user_email;
    
    RETURN 'User data anonymized successfully';
END;
$$ LANGUAGE plpgsql;

-- Create a function to delete expired data
CREATE OR REPLACE FUNCTION delete_expired_data()
RETURNS TEXT AS $$
BEGIN
    -- Delete expired researcher records
    DELETE FROM researchers 
    WHERE data_retention_date < NOW() AND consent_given = FALSE;
    
    -- Delete expired user records
    DELETE FROM users 
    WHERE data_retention_date < NOW() AND consent_given = FALSE;
    
    RETURN 'Expired data deletion completed';
END;
$$ LANGUAGE plpgsql;

-- Add comments for compliance tracking
COMMENT ON COLUMN researchers.consent_given IS 'Indicates if user has given consent for data processing';
COMMENT ON COLUMN researchers.consent_date IS 'Date when user gave consent for data processing';
COMMENT ON COLUMN researchers.data_retention_date IS 'Date until which data will be retained as per DPDP compliance';
COMMENT ON COLUMN researchers.privacy_settings IS 'JSON object containing privacy settings for the researcher';

COMMIT;