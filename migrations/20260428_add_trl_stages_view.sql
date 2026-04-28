-- K-3: expose a short, stable TRL view for generated SQL.
-- Source table from db_struct.sql:
-- innovations_at_various_stages_of_technology_readiness_level

CREATE OR REPLACE VIEW trl_stages AS
SELECT
    innovation_name,
    stage_of_technology,
    stage_of_technology AS trl_level,
    financial_year,
    institute,
    as_on_year,
    id
FROM innovations_at_various_stages_of_technology_readiness_level;
