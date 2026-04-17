-- Migration: Neon branching strategy setup
-- Description: Configure database for optimal Neon branching strategy

BEGIN;

-- Create a function to get the current branch name
-- This is useful for audit trails and debugging
CREATE OR REPLACE FUNCTION get_current_branch()
RETURNS TEXT AS $$
BEGIN
    -- This would typically be set by the application or environment
    -- For now we'll return a default value
    RETURN COALESCE(current_setting('neon.branch', true), 'main');
END;
$$ LANGUAGE plpgsql;

-- Add branch tracking to audit log
ALTER TABLE audit_log
ADD COLUMN IF NOT EXISTS branch_name TEXT DEFAULT '';

-- Create a function to automatically set branch name on insert
CREATE OR REPLACE FUNCTION set_branch_name()
RETURNS TRIGGER AS $$
BEGIN
    NEW.branch_name := get_current_branch();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically set branch name
DROP TRIGGER IF EXISTS set_audit_log_branch ON audit_log;
CREATE TRIGGER set_audit_log_branch
    BEFORE INSERT ON audit_log
    FOR EACH ROW
    EXECUTE FUNCTION set_branch_name();

-- Add comments to track schema changes for branching
COMMENT ON TABLE institutions IS 'Branch: main - Table for research institutions';
COMMENT ON TABLE researchers IS 'Branch: main - Table for researchers';
COMMENT ON TABLE labs IS 'Branch: main - Table for research labs';
COMMENT ON TABLE publications IS 'Branch: main - Table for research publications';
COMMENT ON TABLE funding IS 'Branch: main - Table for research funding information';
COMMENT ON TABLE topics IS 'Branch: main - Table for research topics taxonomy';

-- Create a view to monitor branch-specific data
CREATE OR REPLACE VIEW v_branch_data_stats AS
SELECT 
    get_current_branch() as branch_name,
    'institutions' as table_name,
    COUNT(*) as record_count
FROM institutions
UNION ALL
SELECT 
    get_current_branch() as branch_name,
    'researchers' as table_name,
    COUNT(*) as record_count
FROM researchers
UNION ALL
SELECT 
    get_current_branch() as branch_name,
    'labs' as table_name,
    COUNT(*) as record_count
FROM labs
UNION ALL
SELECT 
    get_current_branch() as branch_name,
    'publications' as table_name,
    COUNT(*) as record_count
FROM publications
UNION ALL
SELECT 
    get_current_branch() as branch_name,
    'funding' as table_name,
    COUNT(*) as record_count
FROM funding;

-- Add branch information to the users table
ALTER TABLE users
ADD COLUMN IF NOT EXISTS created_branch TEXT DEFAULT '';

-- Create an index on branch information for audit purposes
CREATE INDEX IF NOT EXISTS idx_audit_log_branch ON audit_log(branch_name);

COMMIT;