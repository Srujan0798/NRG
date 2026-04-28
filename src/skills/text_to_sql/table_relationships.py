"""Table Relationships — Foreign key definitions across all 58 PostgreSQL tables.

This module documents FK relationships extracted from db_struct.sql for JOIN path inference.
Not all tables have explicit FK constraints (some use application-level joins).
"""

from typing import Dict, List, Set

TABLE_RELATIONSHIPS: Dict[str, List[Dict[str, str]]] = {
    "nirf_extracted_table": [
        {
            "from_column": "pdf_record_id",
            "to_table": "nirf_pdf_record",
            "to_column": "id",
            "relationship": "many-to-one",
            "join_type": "INNER",
            "cardinality": "N:1",
        }
    ],
    "nirf_table_row": [
        {
            "from_column": "table_id",
            "to_table": "nirf_extracted_table",
            "to_column": "id",
            "relationship": "many-to-one",
            "join_type": "INNER",
            "cardinality": "N:1",
        }
    ],
    "auth_group_permissions": [
        {
            "from_column": "group_id",
            "to_table": "auth_group",
            "to_column": "id",
            "relationship": "many-to-one",
            "join_type": "INNER",
            "cardinality": "N:1",
        },
        {
            "from_column": "permission_id",
            "to_table": "auth_permission",
            "to_column": "id",
            "relationship": "many-to-one",
            "join_type": "INNER",
            "cardinality": "N:1",
        },
    ],
    "auth_user_groups": [
        {
            "from_column": "user_id",
            "to_table": "auth_user",
            "to_column": "id",
            "relationship": "many-to-one",
            "join_type": "INNER",
            "cardinality": "N:1",
        },
        {
            "from_column": "group_id",
            "to_table": "auth_group",
            "to_column": "id",
            "relationship": "many-to-one",
            "join_type": "INNER",
            "cardinality": "N:1",
        },
    ],
    "auth_user_user_permissions": [
        {
            "from_column": "user_id",
            "to_table": "auth_user",
            "to_column": "id",
            "relationship": "many-to-one",
            "join_type": "INNER",
            "cardinality": "N:1",
        },
        {
            "from_column": "permission_id",
            "to_table": "auth_permission",
            "to_column": "id",
            "relationship": "many-to-one",
            "join_type": "INNER",
            "cardinality": "N:1",
        },
    ],
    "django_admin_log": [
        {
            "from_column": "user_id",
            "to_table": "auth_user",
            "to_column": "id",
            "relationship": "many-to-one",
            "join_type": "LEFT",
            "cardinality": "N:1",
        },
        {
            "from_column": "content_type_id",
            "to_table": "django_content_type",
            "to_column": "id",
            "relationship": "many-to-one",
            "join_type": "LEFT",
            "cardinality": "N:1",
        },
    ],
}

APPLICATION_JOINS: Dict[str, List[Dict[str, str]]] = {
    "innovation_grant_from_govt": [
        {
            "from_column": "institute",
            "to_table": "tb_institute_mstr",
            "to_column": "institute_name",
            "relationship": "application-level",
            "join_type": "LEFT",
            "cardinality": "N:1",
            "note": "No FK constraint; join on institute name for institute details",
        },
        {
            "from_column": "institute",
            "to_table": "academic_courses_details",
            "to_column": "institute",
            "relationship": "application-level",
            "join_type": "LEFT",
            "cardinality": "N:1",
            "note": "Used in Q13, Q14 for correlating grants with courses",
        },
        {
            "from_column": "institute",
            "to_table": "incubation_details",
            "to_column": "institute",
            "relationship": "application-level",
            "join_type": "LEFT",
            "cardinality": "N:1",
            "note": "Used in Q13 for correlation analysis",
        },
        {
            "from_column": "institute",
            "to_table": "financial_expenses_capital",
            "to_column": "institute",
            "relationship": "application-level",
            "join_type": "LEFT",
            "cardinality": "N:1",
            "note": "Used in Q14",
        },
        {
            "from_column": "institute",
            "to_table": "combined_ipo_patent_data",
            "to_column": "applicants",
            "relationship": "application-level",
            "join_type": "LEFT",
            "cardinality": "N:1",
            "note": "Q7 join key is applicants (not institute); case-insensitive trim required",
        },
    ],
    "academic_courses_details": [
        {
            "from_column": "institute",
            "to_table": "tb_institute_mstr",
            "to_column": "institute_name",
            "relationship": "application-level",
            "join_type": "LEFT",
            "cardinality": "N:1",
            "note": "For institute metadata lookup",
        },
        {
            "from_column": "institute",
            "to_table": "innovation_grant_from_govt",
            "to_column": "institute",
            "relationship": "application-level",
            "join_type": "LEFT",
            "cardinality": "N:1",
            "note": "Used in Q13, Q14",
        },
        {
            "from_column": "institute",
            "to_table": "incubation_details",
            "to_column": "institute",
            "relationship": "application-level",
            "join_type": "LEFT",
            "cardinality": "N:1",
            "note": "Used in Q13",
        },
        {
            "from_column": "institute",
            "to_table": "financial_expenses_capital",
            "to_column": "institute",
            "relationship": "application-level",
            "join_type": "LEFT",
            "cardinality": "N:1",
            "note": "Used in Q14",
        },
    ],
    "incubation_details": [
        {
            "from_column": "institute",
            "to_table": "tb_institute_mstr",
            "to_column": "institute_name",
            "relationship": "application-level",
            "join_type": "LEFT",
            "cardinality": "N:1",
            "note": "Institute metadata",
        },
        {
            "from_column": "institute",
            "to_table": "academic_courses_details",
            "to_column": "institute",
            "relationship": "application-level",
            "join_type": "LEFT",
            "cardinality": "N:1",
            "note": "Q13 correlation with courses",
        },
        {
            "from_column": "institute",
            "to_table": "innovation_grant_from_govt",
            "to_column": "institute",
            "relationship": "application-level",
            "join_type": "LEFT",
            "cardinality": "N:1",
            "note": "Grant correlation",
        },
    ],
    "financial_expenses_capital": [
        {
            "from_column": "institute",
            "to_table": "tb_institute_mstr",
            "to_column": "institute_name",
            "relationship": "application-level",
            "join_type": "LEFT",
            "cardinality": "N:1",
            "note": "Institute metadata",
        },
        {
            "from_column": "institute",
            "to_table": "academic_courses_details",
            "to_column": "institute",
            "relationship": "application-level",
            "join_type": "LEFT",
            "cardinality": "N:1",
            "note": "Q14 correlation with courses",
        },
    ],
    "financial_expenses_operational": [
        {
            "from_column": "institute",
            "to_table": "tb_institute_mstr",
            "to_column": "institute_name",
            "relationship": "application-level",
            "join_type": "LEFT",
            "cardinality": "N:1",
            "note": "Institute metadata; used in Q16",
        },
        {
            "from_column": "institute",
            "to_table": "innovation_grant_from_govt",
            "to_column": "institute",
            "relationship": "application-level",
            "join_type": "LEFT",
            "cardinality": "N:1",
            "note": "Q16 correlation with grants",
        },
    ],
    "combined_ipo_patent_data": [
        {
            "from_column": "applicants",
            "to_table": "innovation_grant_from_govt",
            "to_column": "institute",
            "relationship": "application-level",
            "join_type": "LEFT",
            "cardinality": "N:1",
            "note": "Q7 join on applicants (case-insensitive, trim whitespace)",
        },
        {
            "from_column": "university_name",
            "to_table": "tb_institute_mstr",
            "to_column": "institute_name",
            "relationship": "application-level",
            "join_type": "LEFT",
            "cardinality": "N:1",
            "note": "Alternative join key",
        },
    ],
    "trl_stages": [
        {
            "from_column": "institute",
            "to_table": "tb_institute_mstr",
            "to_column": "institute_name",
            "relationship": "application-level",
            "join_type": "LEFT",
            "cardinality": "N:1",
            "note": "Institute metadata; used in Q5, Q6, Q17",
        },
    ],
    "patents_details": [
        {
            "from_column": "institute",
            "to_table": "tb_institute_mstr",
            "to_column": "institute_name",
            "relationship": "application-level",
            "join_type": "LEFT",
            "cardinality": "N:1",
            "note": "Institute metadata",
        },
    ],
    "phd_students": [
        {
            "from_column": "institute",
            "to_table": "tb_institute_mstr",
            "to_column": "institute_name",
            "relationship": "application-level",
            "join_type": "LEFT",
            "cardinality": "N:1",
            "note": "Institute metadata",
        },
    ],
    "placements_and_higher_studies": [
        {
            "from_column": "institute",
            "to_table": "tb_institute_mstr",
            "to_column": "institute_name",
            "relationship": "application-level",
            "join_type": "LEFT",
            "cardinality": "N:1",
            "note": "Institute metadata",
        },
    ],
    "sanctioned_intake": [
        {
            "from_column": "institute",
            "to_table": "tb_institute_mstr",
            "to_column": "institute_name",
            "relationship": "application-level",
            "join_type": "LEFT",
            "cardinality": "N:1",
            "note": "Institute metadata",
        },
    ],
    "actual_student_strength": [
        {
            "from_column": "institute",
            "to_table": "tb_institute_mstr",
            "to_column": "institute_name",
            "relationship": "application-level",
            "join_type": "LEFT",
            "cardinality": "N:1",
            "note": "Institute metadata",
        },
    ],
    "seed_funding": [
        {
            "from_column": "institute",
            "to_table": "tb_institute_mstr",
            "to_column": "institute_name",
            "relationship": "application-level",
            "join_type": "LEFT",
            "cardinality": "N:1",
            "note": "Startup institute",
        },
    ],
    "startup_receiving_vc_investment": [
        {
            "from_column": "institute",
            "to_table": "tb_institute_mstr",
            "to_column": "institute_name",
            "relationship": "application-level",
            "join_type": "LEFT",
            "cardinality": "N:1",
            "note": "Startup institute",
        },
    ],
    "startup_recognition": [
        {
            "from_column": "institute",
            "to_table": "tb_institute_mstr",
            "to_column": "institute_name",
            "relationship": "application-level",
            "join_type": "LEFT",
            "cardinality": "N:1",
            "note": "Startup institute",
        },
    ],
    "startups_turnover_50_lacs": [
        {
            "from_column": "institute",
            "to_table": "tb_institute_mstr",
            "to_column": "institute_name",
            "relationship": "application-level",
            "join_type": "LEFT",
            "cardinality": "N:1",
            "note": "Startup institute",
        },
    ],
    "fdi_investment": [
        {
            "from_column": "institute",
            "to_table": "tb_institute_mstr",
            "to_column": "institute_name",
            "relationship": "application-level",
            "join_type": "LEFT",
            "cardinality": "N:1",
            "note": "Startup institute",
        },
    ],
    "faculty_details": [
        {
            "from_column": "institute",
            "to_table": "tb_institute_mstr",
            "to_column": "institute_name",
            "relationship": "application-level",
            "join_type": "LEFT",
            "cardinality": "N:1",
            "note": "Faculty institute",
        },
    ],
    "faculty_strength": [
        {
            "from_column": "institute",
            "to_table": "tb_institute_mstr",
            "to_column": "institute_name",
            "relationship": "application-level",
            "join_type": "LEFT",
            "cardinality": "N:1",
            "note": "Faculty institute",
        },
    ],
    "fdp_details": [
        {
            "from_column": "institute",
            "to_table": "tb_institute_mstr",
            "to_column": "institute_name",
            "relationship": "application-level",
            "join_type": "LEFT",
            "cardinality": "N:1",
            "note": "FDP institute",
        },
    ],
    "expertise": [
        {
            "from_column": "institute",
            "to_table": "tb_institute_mstr",
            "to_column": "institute_name",
            "relationship": "application-level",
            "join_type": "LEFT",
            "cardinality": "N:1",
            "note": "Faculty institute",
        },
        {
            "from_column": "department",
            "to_table": "master_expertise",
            "to_column": "department",
            "relationship": "application-level",
            "join_type": "LEFT",
            "cardinality": "N:1",
            "note": "Department lookup",
        },
    ],
    "research_consultancy_details_consultancy": [
        {
            "from_column": "institute",
            "to_table": "tb_institute_mstr",
            "to_column": "institute_name",
            "relationship": "application-level",
            "join_type": "LEFT",
            "cardinality": "N:1",
            "note": "Consultancy institute",
        },
    ],
    "research_consultancy_details_sponsered": [
        {
            "from_column": "institute",
            "to_table": "tb_institute_mstr",
            "to_column": "institute_name",
            "relationship": "application-level",
            "join_type": "LEFT",
            "cardinality": "N:1",
            "note": "Sponsored research institute",
        },
    ],
}

INDEPENDENT_TABLES: Set[str] = {
    "auth_group",
    "auth_permission",
    "auth_user",
    "django_content_type",
    "django_migrations",
    "django_session",
    "user_registration",
    "user_registration_old",
    "tb_institute_mstr",
    "tb_institute_scrap_data_url",
    "tb_goi_ministries_mstr",
    "tb_academic_year_mstr",
    "tb_course_program_types",
    "master_expertise",
    "package_data",
    "role_data",
    "scraped_data",
    "scraped_data_save",
    "scraped_raw_data",
    "advance_search_data",
    "advance_search_data_15_12",
    "advance_search_data_old",
    "ipo_patent_details_flat",
    "ipo_patent_details_flat_old",
    "combined_ipo_patent_data_old",
    "founders_of_fortune_500_companies",
    "adv_se",
    "nirf_pdf_record",
    "startup_recognition_old",
    "innovations_at_various_stages_of_technology_readiness_level",
}


def get_relationship(table_name: str) -> List[Dict[str, str]]:
    """Get FK relationships for a table."""
    return TABLE_RELATIONSHIPS.get(table_name, [])


def get_application_joins(table_name: str) -> List[Dict[str, str]]:
    """Get application-level joins (no FK constraint) for a table."""
    return APPLICATION_JOINS.get(table_name, [])


def get_all_joins(table_name: str) -> List[Dict[str, str]]:
    """Get all join paths for a table (FK + application-level)."""
    return get_relationship(table_name) + get_application_joins(table_name)


def find_join_path(
    from_table: str, to_table: str
) -> List[Dict[str, str]] | None:
    """Find the join path between two tables.

    Returns list of join segments if path exists, None otherwise.
    Supports direct joins and single-hop indirect joins.
    """
    direct = get_all_joins(from_table)
    for join in direct:
        if join["to_table"] == to_table:
            return [join]

    for join in direct:
        intermediate = join["to_table"]
        if intermediate == to_table:
            continue
        indirect = get_all_joins(intermediate)
        for ijoin in indirect:
            if ijoin["to_table"] == to_table:
                return [join, ijoin]

    return None


def get_tables_with_explicit_fk() -> Set[str]:
    """Return set of tables that have FK constraints defined."""
    return set(TABLE_RELATIONSHIPS.keys())


def get_tables_with_app_joins() -> Set[str]:
    """Return set of tables that have application-level joins."""
    return set(APPLICATION_JOINS.keys())


def get_tables_with_any_joins() -> Set[str]:
    """Return set of tables that have any join relationships."""
    return get_tables_with_explicit_fk() | get_tables_with_app_joins()


def get_join_candidates(table_name: str) -> Set[str]:
    """Get tables that can be joined with the given table."""
    joins = get_all_joins(table_name)
    return {j["to_table"] for j in joins}


ALL_58_TABLES: Set[str] = {
    "academic_courses_details",
    "actual_student_strength",
    "adv_se",
    "advance_search_data",
    "advance_search_data_15_12",
    "advance_search_data_old",
    "auth_group",
    "auth_group_permissions",
    "auth_permission",
    "auth_user",
    "auth_user_groups",
    "auth_user_user_permissions",
    "combined_ipo_patent_data",
    "combined_ipo_patent_data_old",
    "django_admin_log",
    "django_content_type",
    "django_migrations",
    "django_session",
    "expertise",
    "faculty_details",
    "faculty_strength",
    "fdi_investment",
    "fdp_details",
    "financial_expenses_capital",
    "financial_expenses_operational",
    "founders_of_fortune_500_companies",
    "incubation_details",
    "innovation_grant_from_govt",
    "trl_stages",
    "ipo_patent_details_flat",
    "ipo_patent_details_flat_old",
    "master_expertise",
    "nirf_extracted_table",
    "nirf_pdf_record",
    "nirf_table_row",
    "package_data",
    "patents_details",
    "phd_students",
    "placements_and_higher_studies",
    "research_consultancy_details_consultancy",
    "research_consultancy_details_sponsered",
    "role_data",
    "sanctioned_intake",
    "scraped_data",
    "scraped_data_save",
    "scraped_raw_data",
    "seed_funding",
    "startup_receiving_vc_investment",
    "startup_recognition",
    "startup_recognition_old",
    "startups_turnover_50_lacs",
    "tb_academic_year_mstr",
    "tb_course_program_types",
    "tb_goi_ministries_mstr",
    "tb_institute_mstr",
    "tb_institute_scrap_data_url",
    "user_registration",
    "user_registration_old",
}


DHAIRYA_QUERY_JOINS: Dict[int, List[Dict[str, str]]] = {
    1: [],
    2: [],
    3: [],
    4: [],
    5: [],
    6: [],
    7: [
        {
            "from_table": "innovation_grant_from_govt",
            "to_table": "combined_ipo_patent_data",
            "join_on": "institute = applicants (case-insensitive)",
            "type": "application-level",
        }
    ],
    8: [],
    9: [],
    10: [],
    11: [],
    12: [],
    13: [
        {
            "from_table": "academic_courses_details",
            "to_table": "incubation_details",
            "join_on": "institute",
            "type": "application-level",
        }
    ],
    14: [
        {
            "from_table": "academic_courses_details",
            "to_table": "financial_expenses_capital",
            "join_on": "institute",
            "type": "application-level",
        }
    ],
    15: [],
    16: [
        {
            "from_table": "innovation_grant_from_govt",
            "to_table": "financial_expenses_operational",
            "join_on": "institute",
            "type": "application-level",
        }
    ],
    17: [],
}
