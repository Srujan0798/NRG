"""Database optimization: composite indexes, materialized views, tier views, data quality

Revision ID: 0006
Revises: 0005
Create Date: 2025-01-15 00:00:00.000000

This migration adds:
- Composite indexes for common query patterns (state+domain, institution+year)
- Materialized views for expensive aggregations
- Tier-filtered views (public_tier1, government_tier2, industry_tier3)
- Institution name normalization mapping
- Researcher deduplication helper tables
- Connection pooling optimized settings
"""

from typing import Sequence, Union

from alembic import op


revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    _create_composite_indexes()
    _create_materialized_views()
    _create_tier_views()
    _create_institution_normalization()
    _create_researcher_dedup_tables()
    _optimize_connection_pooling()


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS v_researchers_tier1")
    op.execute("DROP VIEW IF EXISTS v_researchers_tier2")
    op.execute("DROP VIEW IF EXISTS v_researchers_tier3")
    op.execute("DROP VIEW IF EXISTS v_publications_tier1")
    op.execute("DROP VIEW IF EXISTS v_publications_tier2")
    op.execute("DROP VIEW IF EXISTS v_publications_tier3")
    op.execute("DROP VIEW IF EXISTS v_funding_tier1")
    op.execute("DROP VIEW IF EXISTS v_funding_tier2")
    op.execute("DROP VIEW IF EXISTS v_funding_tier3")
    op.execute("DROP VIEW IF EXISTS v_labs_tier1")
    op.execute("DROP VIEW IF EXISTS v_labs_tier2")
    op.execute("DROP VIEW IF EXISTS v_labs_tier3")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_researchers_per_state")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_researchers_per_area")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_publications_per_year")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_publications_per_area")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_funding_per_agency")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_researcher_stats")
    op.execute("DROP TABLE IF EXISTS institution_name_normalization")
    op.execute("DROP TABLE IF EXISTS researcher_dedup_candidates")
    op.execute("DROP TABLE IF EXISTS researcher_id_mapping")
    op.execute("DROP INDEX IF EXISTS idx_researchers_state_area")
    op.execute("DROP INDEX IF EXISTS idx_researchers_institution_research_area")
    op.execute("DROP INDEX IF EXISTS idx_publications_year_research_area")
    op.execute("DROP INDEX IF EXISTS idx_publications_author_year")
    op.execute("DROP INDEX IF EXISTS idx_funding_researcher_fiscal")
    op.execute("DROP INDEX IF EXISTS idx_funding_agency_fiscal")
    op.execute("DROP INDEX IF EXISTS idx_labs_institution_area")
    op.execute("DROP INDEX IF EXISTS idx_projects_status_research_area")
    op.execute("DROP INDEX IF EXISTS idx_collaborations_country_type")


def _create_composite_indexes() -> None:
    """Create composite indexes for common query patterns."""

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_researchers_state_area
        ON researchers(state, research_area)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_researchers_institution_research_area
        ON researchers(institution_id, research_area)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_publications_year_research_area
        ON publications(year, research_area)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_publications_author_year
        ON publications(year, citations DESC)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_funding_researcher_fiscal
        ON funding_records(researcher_id, fiscal_year)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_funding_agency_fiscal
        ON funding_records(agency, fiscal_year)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_labs_institution_area
        ON labs(institution_id, research_area)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_projects_status_research_area
        ON projects(status, research_area)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_collaborations_country_type
        ON collaborations(partner_country, collaboration_type)
    """)


def _create_materialized_views() -> None:
    """Create materialized views for expensive aggregations."""

    op.execute("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_researchers_per_state AS
        SELECT
            state,
            research_area,
            COUNT(*) as researcher_count,
            AVG(h_index) as avg_h_index,
            SUM(total_funding_received_inr_crores) as total_funding_crores
        FROM researchers
        WHERE state IS NOT NULL
        GROUP BY state, research_area
        ORDER BY researcher_count DESC
    """)

    op.execute("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_researchers_per_area AS
        SELECT
            research_area,
            COUNT(*) as researcher_count,
            COUNT(DISTINCT institution_id) as institution_count,
            AVG(h_index) as avg_h_index,
            AVG(years_experience) as avg_experience
        FROM researchers
        WHERE research_area IS NOT NULL
        GROUP BY research_area
        ORDER BY researcher_count DESC
    """)

    op.execute("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_publications_per_year AS
        SELECT
            year,
            research_area,
            COUNT(*) as publication_count,
            SUM(citations) as total_citations,
            AVG(impact_factor) as avg_impact_factor
        FROM publications
        WHERE year IS NOT NULL
        GROUP BY year, research_area
        ORDER BY year DESC, publication_count DESC
    """)

    op.execute("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_publications_per_area AS
        SELECT
            research_area,
            COUNT(*) as publication_count,
            SUM(citations) as total_citations,
            AVG(impact_factor) as avg_impact_factor,
            COUNT(DISTINCT researcher_ids) as researcher_count
        FROM publications
        WHERE research_area IS NOT NULL
        GROUP BY research_area
        ORDER BY publication_count DESC
    """)

    op.execute("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_funding_per_agency AS
        SELECT
            agency,
            fiscal_year,
            COUNT(*) as funding_count,
            SUM(amount) as total_amount,
            AVG(amount) as avg_amount
        FROM funding_records
        WHERE agency IS NOT NULL
        GROUP BY agency, fiscal_year
        ORDER BY total_amount DESC
    """)

    op.execute("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_researcher_stats AS
        SELECT
            r.researcher_id,
            r.name,
            r.state,
            r.research_area,
            r.institution_id,
            r.h_index,
            r.total_funding_received_inr_crores,
            COUNT(DISTINCT rp.publication_id) as publication_count,
            COUNT(DISTINCT fr.funding_id) as funding_count,
            COUNT(DISTINCT l.lab_id) as lab_count
        FROM researchers r
        LEFT JOIN researcher_publications rp ON r.researcher_id = rp.researcher_id
        LEFT JOIN funding_records fr ON r.researcher_id = fr.researcher_id
        LEFT JOIN researcher_labs rl ON r.researcher_id = rl.researcher_id
        LEFT JOIN labs l ON rl.lab_id = l.lab_id
        GROUP BY r.researcher_id, r.name, r.state, r.research_area,
                 r.institution_id, r.h_index, r.total_funding_received_inr_crores
        ORDER BY publication_count DESC
    """)

    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_researchers_state ON mv_researchers_per_state(state, research_area)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_researchers_area ON mv_researchers_per_area(research_area)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_publications_year ON mv_publications_per_year(year, research_area)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_publications_area ON mv_publications_per_area(research_area)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_funding_agency ON mv_funding_per_agency(agency, fiscal_year)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_mv_researcher_stats_id ON mv_researcher_stats(researcher_id)")


def _create_tier_views() -> None:
    """Create tier-filtered views for different access levels."""

    op.execute("""
        CREATE OR REPLACE VIEW v_researchers_tier1 AS
        SELECT
            researcher_id,
            name,
            institution_id,
            department,
            state,
            research_area,
            secondary_research_areas,
            years_experience,
            year_joined,
            h_index,
            total_funding_received_inr_crores,
            email,
            phone,
            orcid,
            created_at,
            updated_at
        FROM researchers
        WHERE access_tier <= 1
        WITH LOCAL CHECK OPTION
    """)

    op.execute("""
        CREATE OR REPLACE VIEW v_researchers_tier2 AS
        SELECT
            researcher_id,
            name,
            institution_id,
            department,
            state,
            research_area,
            secondary_research_areas,
            years_experience,
            year_joined,
            h_index,
            total_funding_received_inr_crores,
            email,
            orcid,
            created_at,
            updated_at
        FROM researchers
        WHERE access_tier <= 2
        WITH LOCAL CHECK OPTION
    """)

    op.execute("""
        CREATE OR REPLACE VIEW v_researchers_tier3 AS
        SELECT
            researcher_id,
            name,
            institution_id,
            department,
            state,
            research_area,
            secondary_research_areas,
            years_experience,
            year_joined,
            h_index,
            orcid,
            created_at,
            updated_at
        FROM researchers
        WHERE access_tier <= 3
        WITH LOCAL CHECK OPTION
    """)

    op.execute("""
        CREATE OR REPLACE VIEW v_publications_tier1 AS
        SELECT
            publication_id,
            title,
            abstract,
            authors,
            researcher_ids,
            venue,
            year,
            volume,
            issue,
            pages,
            doi,
            pmid,
            citations,
            impact_factor,
            publication_type,
            research_area,
            created_at,
            updated_at
        FROM publications
        WHERE access_tier <= 1
        WITH LOCAL CHECK OPTION
    """)

    op.execute("""
        CREATE OR REPLACE VIEW v_publications_tier2 AS
        SELECT
            publication_id,
            title,
            abstract,
            authors,
            researcher_ids,
            venue,
            year,
            volume,
            issue,
            pages,
            doi,
            pmid,
            citations,
            impact_factor,
            publication_type,
            research_area,
            created_at,
            updated_at
        FROM publications
        WHERE access_tier <= 2
        WITH LOCAL CHECK OPTION
    """)

    op.execute("""
        CREATE OR REPLACE VIEW v_publications_tier3 AS
        SELECT
            publication_id,
            title,
            authors,
            researcher_ids,
            venue,
            year,
            citations,
            publication_type,
            research_area,
            created_at,
            updated_at
        FROM publications
        WHERE access_tier <= 3
        WITH LOCAL CHECK OPTION
    """)

    op.execute("""
        CREATE OR REPLACE VIEW v_funding_tier1 AS
        SELECT
            funding_id,
            researcher_id,
            institution_id,
            project_id,
            agency,
            amount,
            fiscal_year,
            start_date,
            end_date,
            title,
            created_at,
            updated_at
        FROM funding_records
        WHERE access_tier <= 1
        WITH LOCAL CHECK OPTION
    """)

    op.execute("""
        CREATE OR REPLACE VIEW v_funding_tier2 AS
        SELECT
            funding_id,
            researcher_id,
            institution_id,
            project_id,
            agency,
            amount,
            fiscal_year,
            start_date,
            end_date,
            title,
            created_at,
            updated_at
        FROM funding_records
        WHERE access_tier <= 2
        WITH LOCAL CHECK OPTION
    """)

    op.execute("""
        CREATE OR REPLACE VIEW v_funding_tier3 AS
        SELECT
            funding_id,
            researcher_id,
            project_id,
            agency,
            fiscal_year,
            start_date,
            end_date,
            title,
            created_at,
            updated_at
        FROM funding_records
        WHERE access_tier <= 3
        WITH LOCAL CHECK OPTION
    """)

    op.execute("""
        CREATE OR REPLACE VIEW v_labs_tier1 AS
        SELECT
            lab_id,
            name,
            institution_id,
            research_area,
            research_focus_areas,
            established_year,
            location_state,
            director_researcher_id,
            website,
            created_at,
            updated_at
        FROM labs
        WHERE access_tier <= 1
        WITH LOCAL CHECK OPTION
    """)

    op.execute("""
        CREATE OR REPLACE VIEW v_labs_tier2 AS
        SELECT
            lab_id,
            name,
            institution_id,
            research_area,
            research_focus_areas,
            established_year,
            location_state,
            director_researcher_id,
            website,
            created_at,
            updated_at
        FROM labs
        WHERE access_tier <= 2
        WITH LOCAL CHECK OPTION
    """)

    op.execute("""
        CREATE OR REPLACE VIEW v_labs_tier3 AS
        SELECT
            lab_id,
            name,
            institution_id,
            research_area,
            research_focus_areas,
            established_year,
            location_state,
            created_at,
            updated_at
        FROM labs
        WHERE access_tier <= 3
        WITH LOCAL CHECK OPTION
    """)


def _create_institution_normalization() -> None:
    """Create institution name normalization mapping table."""

    op.execute("""
        CREATE TABLE IF NOT EXISTS institution_name_normalization (
            normalization_id INTEGER PRIMARY KEY AUTOINCREMENT,
            canonical_name VARCHAR(255) NOT NULL,
            alternate_name VARCHAR(255) NOT NULL UNIQUE,
            institution_type VARCHAR(50),
            state VARCHAR(100),
            country VARCHAR(10) DEFAULT 'IN',
            confidence_score REAL DEFAULT 1.0,
            is_verified BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_inst_norm_canonical
        ON institution_name_normalization(canonical_name)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_inst_norm_alternate
        ON institution_name_normalization(alternate_name)
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS institution_aliases (
            alias_id INTEGER PRIMARY KEY AUTOINCREMENT,
            institution_id VARCHAR(36) REFERENCES institutions(institution_id),
            alias VARCHAR(255) NOT NULL UNIQUE,
            alias_type VARCHAR(50) DEFAULT 'common_abbreviation',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_inst_alias_institution
        ON institution_aliases(institution_id)
    """)

    _populate_institution_normalization()


def _populate_institution_normalization() -> None:
    """Populate common IIT and Indian institution name normalizations."""

    iit_normalizations = [
        ("Indian Institute of Technology Bombay", "IIT Bombay", "IIT", "Maharashtra"),
        ("Indian Institute of Technology Bombay", "IITB", "IIT", "Maharashtra"),
        ("Indian Institute of Technology Bombay", "IIT Mumbai", "IIT", "Maharashtra"),
        ("Indian Institute of Technology Delhi", "IIT Delhi", "IIT", "Delhi"),
        ("Indian Institute of Technology Delhi", "IITD", "IIT", "Delhi"),
        ("Indian Institute of Technology Madras", "IIT Madras", "IIT", "Tamil Nadu"),
        ("Indian Institute of Technology Madras", "IITM", "IIT", "Tamil Nadu"),
        ("Indian Institute of Technology Kanpur", "IIT Kanpur", "IIT", "Uttar Pradesh"),
        ("Indian Institute of Technology Kanpur", "IITK", "IIT", "Uttar Pradesh"),
        ("Indian Institute of Technology Kharagpur", "IIT Kharagpur", "IIT", "West Bengal"),
        ("Indian Institute of Technology Kharagpur", "IITKG", "IIT", "West Bengal"),
        ("Indian Institute of Technology Roorkee", "IIT Roorkee", "IIT", "Uttarakhand"),
        ("Indian Institute of Technology Roorkee", "IITR", "IIT", "Uttarakhand"),
        ("Indian Institute of Technology Hyderabad", "IIT Hyderabad", "IIT", "Telangana"),
        ("Indian Institute of Technology Hyderabad", "IITH", "IIT", "Telangana"),
        ("Indian Institute of Technology Gandhinagar", "IIT Gandhinagar", "IIT", "Gujarat"),
        ("Indian Institute of Technology Gandhinagar", "IITGN", "IIT", "Gujarat"),
        ("Indian Institute of Technology Goa", "IIT Goa", "IIT", "Goa"),
        ("Indian Institute of Technology Palakkad", "IIT Palakkad", "IIT", "Kerala"),
        ("Indian Institute of Technology Tirupati", "IIT Tirupati", "IIT", "Andhra Pradesh"),
        ("Indian Institute of Technology (Banaras Hindu University) Varanasi", "IIT BHU", "IIT", "Uttar Pradesh"),
        ("Indian Institute of Technology (Banaras Hindu University) Varanasi", "IIT Varanasi", "IIT", "Uttar Pradesh"),
        ("National Institute of Technology Calicut", "NIT Calicut", "NIT", "Kerala"),
        ("National Institute of Technology Calicut", "NITC", "NIT", "Kerala"),
        ("National Institute of Technology Karnataka", "NIT Karnataka", "NIT", "Karnataka"),
        ("National Institute of Technology Karnataka", "NITK Surathkal", "NIT", "Karnataka"),
        ("National Institute of Technology Warangal", "NIT Warangal", "NIT", "Telangana"),
        ("National Institute of Technology Warangal", "NITW", "NIT", "Telangana"),
        ("National Institute of Technology Rourkela", "NIT Rourkela", "NIT", "Odisha"),
        ("National Institute of Technology Rourkela", "NITR", "NIT", "Odisha"),
        ("National Institute of Technology Trichy", "NIT Tiruchirappalli", "NIT", "Tamil Nadu"),
        ("National Institute of Technology Trichy", "NITT", "NIT", "Tamil Nadu"),
        ("National Institute of Technology Hamirpur", "NIT Hamirpur", "NIT", "Himachal Pradesh"),
        ("National Institute of Technology Jaipur", "NIT Jaipur", "NIT", "Rajasthan"),
        ("National Institute of Technology Jaipur", "MNIT Jaipur", "NIT", "Rajasthan"),
        ("National Institute of Technology Punjab", "NIT Punjab", "NIT", "Punjab"),
        ("National Institute of Technology Punjab", "NITJ", "NIT", "Punjab"),
        ("All India Institute of Medical Sciences New Delhi", "AIIMS Delhi", "Medical", "Delhi"),
        ("All India Institute of Medical Sciences New Delhi", "AIIMS New Delhi", "Medical", "Delhi"),
        ("Indian Institute of Science Bangalore", "IISc Bangalore", "Research Institute", "Karnataka"),
        ("Indian Institute of Science Bangalore", "IISc", "Research Institute", "Karnataka"),
        ("Indian Institute of Science Education and Research Pune", "IISER Pune", "Research Institute", "Maharashtra"),
        ("Indian Institute of Science Education and Research Pune", "IISER", "Research Institute", "Maharashtra"),
        ("Indian Institute of Science Education and Research Mohali", "IISER Mohali", "Research Institute", "Punjab"),
        ("Indian Institute of Science Education and Research Bhopal", "IISER Bhopal", "Research Institute", "Madhya Pradesh"),
        ("Indian Institute of Science Education and Research Kolkata", "IISER Kolkata", "Research Institute", "West Bengal"),
        ("Institute of Chemical Technology", "ICT Mumbai", "Research Institute", "Maharashtra"),
        ("Institute of Chemical Technology", "ICT", "Research Institute", "Maharashtra"),
        ("Jawaharlal Nehru University", "JNU", "University", "Delhi"),
        ("Jawaharlal Nehru University", "JNU New Delhi", "University", "Delhi"),
        ("University of Delhi", "DU", "University", "Delhi"),
        ("University of Delhi", "Delhi University", "University", "Delhi"),
        ("Anna University", "AU Chennai", "University", "Tamil Nadu"),
        ("Anna University", "Anna Univ", "University", "Tamil Nadu"),
        ("Indian Statistical Institute", "ISI Kolkata", "Research Institute", "West Bengal"),
        ("Indian Statistical Institute", "ISI", "Research Institute", "West Bengal"),
    ]

    for canonical, alternate, inst_type, state in iit_normalizations:
        op.execute(
            f"""
            INSERT OR IGNORE INTO institution_name_normalization
            (canonical_name, alternate_name, institution_type, state, is_verified)
            VALUES ('{canonical}', '{alternate}', '{inst_type}', '{state}', 1)
            """
        )


def _create_researcher_dedup_tables() -> None:
    """Create researcher deduplication helper tables."""

    op.execute("""
        CREATE TABLE IF NOT EXISTS researcher_id_mapping (
            mapping_id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_id VARCHAR(36) NOT NULL,
            canonical_id VARCHAR(36) NOT NULL,
            id_namespace VARCHAR(50),
            confidence_score REAL DEFAULT 1.0,
            match_type VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(original_id, id_namespace)
        )
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_researcher_map_original
        ON researcher_id_mapping(original_id)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_researcher_map_canonical
        ON researcher_id_mapping(canonical_id)
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS researcher_dedup_candidates (
            dedup_id INTEGER PRIMARY KEY AUTOINCREMENT,
            researcher_id_1 VARCHAR(36) NOT NULL,
            researcher_id_2 VARCHAR(36) NOT NULL,
            similarity_score REAL,
            match_fields TEXT,
            status VARCHAR(50) DEFAULT 'pending',
            reviewed_at TIMESTAMP,
            reviewed_by VARCHAR(36),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(researcher_id_1, researcher_id_2)
        )
    """)

    op.execute("""
        CREATE INDEX IF EXISTS idx_dedup_status
        ON researcher_dedup_candidates(status)
    """)

    op.execute("""
        CREATE INDEX IF EXISTS idx_dedup_researcher1
        ON researcher_dedup_candidates(researcher_id_1)
    """)

    _populate_researcher_dedup()


def _populate_researcher_dedup() -> None:
    """Populate researcher deduplication by finding matching names + email patterns."""

    op.execute("""
        INSERT OR IGNORE INTO researcher_dedup_candidates
        (researcher_id_1, researcher_id_2, similarity_score, match_fields, status)
        SELECT
            r1.researcher_id,
            r2.researcher_id,
            0.95,
            'email_domain',
            'pending'
        FROM researchers r1
        JOIN researchers r2 ON
            r1.email IS NOT NULL AND r2.email IS NOT NULL
            AND r1.researcher_id < r2.researcher_id
            AND r1.email = r2.email
    """)

    op.execute("""
        INSERT OR IGNORE INTO researcher_dedup_candidates
        (researcher_id_1, researcher_id_2, similarity_score, match_fields, status)
        SELECT
            r1.researcher_id,
            r2.researcher_id,
            0.90,
            'name_institution',
            'pending'
        FROM researchers r1
        JOIN researchers r2 ON
            r1.researcher_id < r2.researcher_id
            AND LOWER(TRIM(r1.name)) = LOWER(TRIM(r2.name))
            AND r1.institution_id IS NOT NULL
            AND r2.institution_id IS NOT NULL
            AND r1.institution_id = r2.institution_id
    """)

    op.execute("""
        INSERT OR IGNORE INTO researcher_dedup_candidates
        (researcher_id_1, researcher_id_2, similarity_score, match_fields, status)
        SELECT
            r1.researcher_id,
            r2.researcher_id,
            0.85,
            'orcid',
            'pending'
        FROM researchers r1
        JOIN researchers r2 ON
            r1.orcid IS NOT NULL AND r2.orcid IS NOT NULL
            AND r1.researcher_id < r2.researcher_id
            AND r1.orcid = r2.orcid
    """)


def _optimize_connection_pooling() -> None:
    """Create optimized connection pooling and query performance settings."""

    op.execute("""
        CREATE TABLE IF NOT EXISTS query_performance_log (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_hash VARCHAR(64) NOT NULL,
            query_text TEXT,
            execution_time_ms REAL,
            planning_time_ms REAL,
            row_count INTEGER,
            cache_hit BOOLEAN,
            executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_query_log_hash
        ON query_performance_log(query_hash)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_query_log_time
        ON query_performance_log(executed_at)
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS slow_query_thresholds (
            threshold_id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_pattern VARCHAR(255) NOT NULL,
            max_acceptable_ms REAL DEFAULT 1000.0,
            optimization_status VARCHAR(50) DEFAULT 'needs_review',
            last_reviewed_at TIMESTAMP,
            review_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_slow_query_pattern
        ON slow_query_thresholds(query_pattern)
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS db_maintenance_log (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            operation_type VARCHAR(50) NOT NULL,
            target_object VARCHAR(255),
            duration_seconds REAL,
            status VARCHAR(50),
            error_message TEXT,
            executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS index_usage_stats (
            stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
            index_name VARCHAR(255) NOT NULL,
            table_name VARCHAR(255) NOT NULL,
            scans_since_last_vacuum INTEGER DEFAULT 0,
            last_scan_at TIMESTAMP,
            is_recommended_drop BOOLEAN DEFAULT FALSE,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)