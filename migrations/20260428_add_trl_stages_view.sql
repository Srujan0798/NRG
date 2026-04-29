-- K-3: expose short, stable TRL views for generated SQL.
-- Source table from db_struct.sql:
-- innovations_at_various_stages_of_technology_readiness_level

CREATE OR REPLACE VIEW trl_stages AS
SELECT
    id,
    institute,
    financial_year,
    stage_of_technology,
    stage_of_technology AS trl_level,
    stage_of_technology AS tech_readiness_stage,
    innovation_name,
    as_on_year,
    NULL::integer AS project_count,
    NULL::numeric AS grant_amount
FROM innovations_at_various_stages_of_technology_readiness_level;

CREATE OR REPLACE VIEW tech_trl_stages AS
SELECT
    id,
    institute,
    financial_year,
    stage_of_technology,
    stage_of_technology AS trl_level,
    stage_of_technology AS tech_readiness_stage,
    innovation_name,
    as_on_year,
    NULL::integer AS project_count,
    NULL::numeric AS grant_amount
FROM innovations_at_various_stages_of_technology_readiness_level;
