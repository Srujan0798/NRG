#!/usr/bin/env python3
"""Seed production tables with minimal sample data (10 rows each).

This script populates the 40 missing tables from db_struct.sql with
synthetic but realistic data. Used for development/staging to enable
Dhairya SQL benchmark queries to execute.

Usage:
    python scripts/seed_production_tables.py [--url DATABASE_URL] [--rows 10]

Tables seeded:
- academic_courses_details
- innovation_grant_from_govt
- innovations_at_various_stages_of_technology_readiness_level
- combined_ipo_patent_data
- incubation_details
- financial_expenses_capital
- financial_expenses_operational
- phd_students, sanctioned_intake, actual_student_strength
- placements_and_higher_studies, package_data, role_data
- faculty_details, faculty_strength, fdp_details, expertise, master_expertise
- seed_funding, startup_receiving_vc_investment, startup_recognition
- startups_turnover_50_lacs, fdi_investment
- nirf_extracted_table, nirf_pdf_record, nirf_table_row
- research_consultancy_details_consultancy, research_consultancy_details_sponsered
- patents_details, ipo_patent_details_flat, ipo_patent_details_flat_old
- combined_ipo_patent_data_old
- scraped_data, scraped_data_save, scraped_raw_data
- advance_search_data, advance_search_data_15_12, advance_search_data_old
- tb_institute_mstr, tb_institute_scrap_data_url, tb_goi_ministries_mstr
- tb_academic_year_mstr, tb_course_program_types
- user_registration, founders_of_fortune_500_companies
- startup_recognition_old
"""

import argparse
import os
import sys
import random
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    Integer,
    MetaData,
    Numeric,
    Table,
    create_engine,
    inspect,
    text,
)

SRC_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SRC_ROOT))


INSTITUTES = [
    "IIT Bombay", "IIT Madras", "IIT Delhi", "IIT Kanpur", "IIT Kharagpur",
    "IIT Hyderabad", "IIT Roorkee", "IIT Guwahati", "IIT Bangalore", "IIT Gandhinagar",
    "NIT Trichy", "NIT Surathkal", "BITS Pilani", "Anna University", "VIT Vellore"
]

IIT_NAMES = [f"IIT {city}" for city in ["Bombay", "Madras", "Delhi", "Kanpur", "Kharagpur",
                                         "Hyderabad", "Roorkee", "Guwahati", "Ropar", "Bhopal"]]

FINANCIAL_YEARS = ["2020-21", "2021-22", "2022-23", "2023-24", "2024-25"]
AS_ON_YEARS = ["2023-24", "2024-25", "2025-26"]

RESEARCH_AREAS = [
    "Artificial Intelligence", "Machine Learning", "Data Science",
    "Robotics", "Internet of Things", "Blockchain",
    "Cybersecurity", "Cloud Computing", "Quantum Computing",
    "Biotechnology", "Materials Science", "Energy Systems"
]

TRL_STAGES = [
    "Level 1", "Level 2", "Level 3", "Level 4", "Level 5",
    "Level 6", "Level 7", "Level 8", "Level 9"
]

COURSE_LEVELS = ["UG", "PG", "PhD", "Diploma", "Certificate"]
PROGRAM_TYPES = ["B.Tech", "M.Tech", "MSc", "MBA", "PhD"]

GOV_ORGS = [
    "DST", "DBT", "AICTE", "UGC", "CSIR", "ICSSR",
    "Ministry of Education", "Ministry of Science & Technology",
    "ICMR", "DRDO", "ISRO"
]


def get_production_table_names() -> list[str]:
    """Return the authoritative production table list from db_struct.sql."""
    db_struct_path = SRC_ROOT / "db_struct.sql"
    content = db_struct_path.read_text()
    return re.findall(r"CREATE TABLE public\.(\w+)", content)


def _fit_string(value: str, max_length: int | None) -> str:
    if not max_length or len(value) <= max_length:
        return value
    suffix = str(abs(hash(value)) % 10000)
    return f"{value[: max_length - len(suffix)]}{suffix}"


def _sample_value(table_name: str, column, row_number: int) -> Any:
    """Generate deterministic seed data compatible with reflected SQLAlchemy types."""
    column_name = column.name
    column_key = f"{table_name}_{column_name}_{row_number}"
    column_type = column.type

    if isinstance(column_type, Boolean):
        return row_number % 2 == 0
    if isinstance(column_type, DateTime):
        return datetime(2024, 1, 1, 12, 0, 0)
    if isinstance(column_type, Date):
        return datetime(2024, 1, 1).date()
    if isinstance(column_type, Integer):
        return row_number
    if isinstance(column_type, (Float, Numeric)):
        return float(row_number * 100)
    if column_type.__class__.__name__.lower() in {"json", "jsonb"}:
        return {"seed": True, "row": row_number}
    if "email" in column_name:
        return _fit_string(f"{column_key}@example.test", getattr(column_type, "length", None))
    if "password" in column_name:
        return _fit_string("seeded-password-hash", getattr(column_type, "length", None))
    if "phone" in column_name or "contact_number" in column_name:
        return _fit_string(f"900000{row_number:04d}", getattr(column_type, "length", None))
    if column_name in {"is_active", "is_staff", "is_superuser", "is_approved"}:
        return row_number % 2 == 1
    return _fit_string(column_key, getattr(column_type, "length", None))


def seed_table_generic(conn, table_name: str, rows: int) -> int:
    """Seed a reflected table with synthetic rows when it is empty."""
    existing_count = conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}"')).scalar_one()
    if existing_count:
        return 0

    metadata = MetaData()
    table = Table(table_name, metadata, autoload_with=conn)
    payload = []
    for row_number in range(1, max(rows, 1) + 1):
        payload.append({column.name: _sample_value(table_name, column, row_number) for column in table.columns})

    conn.execute(table.insert(), payload)
    return len(payload)


def seed_all_production_tables(conn, rows: int = 10) -> dict[str, int]:
    """Seed every table from db_struct.sql that exists in the connected database."""
    live_tables = set(inspect(conn).get_table_names())
    inserted: dict[str, int] = {}
    for table_name in get_production_table_names():
        if table_name not in live_tables:
            continue
        inserted[table_name] = seed_table_generic(conn, table_name, rows)
    return inserted


def random_int(min_val: int, max_val: int) -> int:
    return random.randint(min_val, max_val)


def random_bigint(min_val: int, max_val: int) -> int:
    return random.randint(min_val, max_val)


def seed_academic_courses_details(conn, rows: int = 10):
    print("Seeding academic_courses_details...")
    data = []
    for i in range(rows):
        data.append({
            "financial_year": random.choice(FINANCIAL_YEARS),
            "title_of_course": f"Course {i+1}",
            "course_code": f"COURSE{1000+i}",
            "type_of_course": random.choice(["Core", "Elective", "Lab"]),
            "level_of_course": random.choice(COURSE_LEVELS),
            "course_offering_department": f"Department {random.randint(1,10)}",
            "total_credit_score": f"{random.randint(1,4)}:{random.randint(0,1)}",
            "institute": random.choice(IIT_NAMES),
            "as_on_year": random.choice(AS_ON_YEARS),
            "id": i + 1
        })
    for d in data:
        conn.execute(text("""
            INSERT INTO academic_courses_details
            (financial_year, title_of_course, course_code, type_of_course,
             level_of_course, course_offering_department, total_credit_score,
             institute, as_on_year, id)
            VALUES (:financial_year, :title_of_course, :course_code, :type_of_course,
                    :level_of_course, :course_offering_department, :total_credit_score,
                    :institute, :as_on_year, :id)
        """), d)


def seed_innovation_grant_from_govt(conn, rows: int = 10):
    print("Seeding innovation_grant_from_govt...")
    data = []
    for i in range(rows):
        data.append({
            "gov_organisation_name": random.choice(GOV_ORGS),
            "grant_received": random_bigint(100000, 50000000),
            "year_of_receiving": random.choice(FINANCIAL_YEARS),
            "institute": random.choice(IIT_NAMES),
            "id": i + 1,
            "financial_year": random.choice(FINANCIAL_YEARS)
        })
    for d in data:
        conn.execute(text("""
            INSERT INTO innovation_grant_from_govt
            (gov_organisation_name, grant_received, year_of_receiving, institute, id, financial_year)
            VALUES (:gov_organisation_name, :grant_received, :year_of_receiving, :institute, :id, :financial_year)
        """), d)


def seed_innovations_at_various_stages_of_technology_readiness_level(conn, rows: int = 10):
    print("Seeding innovations_at_various_stages_of_technology_readiness_level...")
    data = []
    for i in range(rows):
        data.append({
            "innovation_name": f"Innovation {i+1}",
            "stage_of_technology": random.choice(TRL_STAGES),
            "financial_year": random.choice(FINANCIAL_YEARS),
            "institute": random.choice(IIT_NAMES),
            "as_on_year": random.choice(AS_ON_YEARS),
            "id": i + 1
        })
    for d in data:
        conn.execute(text("""
            INSERT INTO innovations_at_various_stages_of_technology_readiness_level
            (innovation_name, stage_of_technology, financial_year, institute, as_on_year, id)
            VALUES (:innovation_name, :stage_of_technology, :financial_year, :institute, :as_on_year, :id)
        """), d)


def seed_combined_ipo_patent_data(conn, rows: int = 10):
    print("Seeding combined_ipo_patent_data...")
    data = []
    for i in range(rows):
        data.append({
            "id": i + 1,
            "oid": f"OID{i+1}",
            "application_number": f"2021{1000+i}IND",
            "inserted_at": datetime.now().isoformat(),
            "applicants": random.choice(IIT_NAMES),
            "inventors": f"Dr. Inventor {i+1}",
            "title_of_invention": f"Patent Title {i+1}",
            "title_of_invention_latest": f"Patent Title Updated {i+1}",
            "international_patent_classification": f"H04N{i+1}",
            "international_patent_classification_desc": "Patent classification description",
            "national_classification": f"NC{i+1}",
            "priority_date": "2020-01-15",
            "publication_date": "2021-06-20",
            "grant_date": "2023-03-10" if random.random() > 0.3 else None,
            "status": random.choice(["Granted", "Pending", "Abandoned"]),
            "status_updated_date": "2024-01-01",
            "url": f"https://ipindia.gov.in/patent/{i+1}",
            "field_of_invention": random.choice(RESEARCH_AREAS),
            "ipo_controller_name": "Controller of Patents",
            "ipo_application_type": random.choice(["Ordinary", "PCT"]),
            "ipo_field_of_invention_description": "Field description",
            "designated_states": "IN",
            "primary_applicant_name": f"Applicant {i+1}",
            "primary_applicant_address": f"Address {i+1}",
            "primary_applicant_city": "Mumbai",
            "primary_applicant_state": "Maharashtra",
            "primary_applicant_country": "India",
            "primary_applicant_pincode": f"400{i+1:03d}",
            "primary_applicant_entity": "Educational Institution",
            "primary_applicant_nationality": "Indian",
            "primary_applicant_synonym": f"Synonym{i+1}",
            "all_applicant_names": "Applicant 1, Applicant 2",
            "all_applicant_addresses": "Address 1, Address 2",
            "all_applicant_cities": "Mumbai, Bangalore",
            "all_applicant_nationalities": "Indian",
            "all_applicant_countries": "India",
            "all_applicant_entities": "Educational Institution",
            "all_inventor_names": f"Dr. Inventor {i+1}",
            "all_inventor_addresses": f"Address {i+1}",
            "all_inventor_cities": "Mumbai",
            "all_inventor_nationalities": "Indian",
            "all_inventor_countries": "India"
        })
    for d in data:
        conn.execute(text("""
            INSERT INTO combined_ipo_patent_data
            (id, oid, application_number, inserted_at, applicants, inventors,
             title_of_invention, title_of_invention_latest, international_patent_classification,
             international_patent_classification_desc, national_classification,
             priority_date, publication_date, grant_date, status, status_updated_date,
             url, field_of_invention, ipo_controller_name, ipo_application_type,
             ipo_field_of_invention_description, designated_states,
             primary_applicant_name, primary_applicant_address, primary_applicant_city,
             primary_applicant_state, primary_applicant_country, primary_applicant_pincode,
             primary_applicant_entity, primary_applicant_nationality, primary_applicant_synonym,
             all_applicant_names, all_applicant_addresses, all_applicant_cities,
             all_applicant_nationalities, all_applicant_countries, all_applicant_entities,
             all_inventor_names, all_inventor_addresses, all_inventor_cities,
             all_inventor_nationalities, all_inventor_countries)
            VALUES (:id, :oid, :application_number, :inserted_at, :applicants, :inventors,
                    :title_of_invention, :title_of_invention_latest, :international_patent_classification,
                    :international_patent_classification_desc, :national_classification,
                    :priority_date, :publication_date, :grant_date, :status, :status_updated_date,
                    :url, :field_of_invention, :ipo_controller_name, :ipo_application_type,
                    :ipo_field_of_invention_description, :designated_states,
                    :primary_applicant_name, :primary_applicant_address, :primary_applicant_city,
                    :primary_applicant_state, :primary_applicant_country, :primary_applicant_pincode,
                    :primary_applicant_entity, :primary_applicant_nationality, :primary_applicant_synonym,
                    :all_applicant_names, :all_applicant_addresses, :all_applicant_cities,
                    :all_applicant_nationalities, :all_applicant_countries, :all_applicant_entities,
                    :all_inventor_names, :all_inventor_addresses, :all_inventor_cities,
                    :all_inventor_nationalities, :all_inventor_countries)
        """), d)


def seed_incubation_details(conn, rows: int = 10):
    print("Seeding incubation_details...")
    data = []
    for i in range(rows):
        data.append({
            "financial_year": random.choice(FINANCIAL_YEARS),
            "no_of_pre_incubation_units": random_int(1, 20),
            "expenditure_on_pre_incubation_activities": random_bigint(50000, 500000),
            "income_generated_pre_incubation": random_bigint(100000, 1000000),
            "no_of_incubation_units": random_int(5, 50),
            "expenditure_on_incubation_activities": random_bigint(500000, 5000000),
            "income_generated_incubation": random_bigint(1000000, 10000000),
            "institute": random.choice(IIT_NAMES),
            "as_on_year": random.choice(AS_ON_YEARS),
            "id": i + 1
        })
    for d in data:
        conn.execute(text("""
            INSERT INTO incubation_details
            (financial_year, no_of_pre_incubation_units, expenditure_on_pre_incubation_activities,
             income_generated_pre_incubation, no_of_incubation_units, expenditure_on_incubation_activities,
             income_generated_incubation, institute, as_on_year, id)
            VALUES (:financial_year, :no_of_pre_incubation_units, :expenditure_on_pre_incubation_activities,
                    :income_generated_pre_incubation, :no_of_incubation_units, :expenditure_on_incubation_activities,
                    :income_generated_incubation, :institute, :as_on_year, :id)
        """), d)


def seed_financial_expenses_capital(conn, rows: int = 10):
    print("Seeding financial_expenses_capital...")
    data = []
    for i in range(rows):
        data.append({
            "id": i + 1,
            "financial_year": random.choice(FINANCIAL_YEARS),
            "library": random_bigint(100000, 5000000),
            "equipment": random_bigint(500000, 20000000),
            "workshops": random_bigint(50000, 1000000),
            "other_capital": random_bigint(100000, 5000000),
            "total_capital": random_bigint(1000000, 30000000),
            "institute": random.choice(IIT_NAMES)
        })
    for d in data:
        conn.execute(text("""
            INSERT INTO financial_expenses_capital
            (id, financial_year, library, equipment, workshops, other_capital, total_capital, institute)
            VALUES (:id, :financial_year, :library, :equipment, :workshops, :other_capital, :total_capital, :institute)
        """), d)


def seed_financial_expenses_operational(conn, rows: int = 10):
    print("Seeding financial_expenses_operational...")
    data = []
    for i in range(rows):
        data.append({
            "id": i + 1,
            "financial_year": random.choice(FINANCIAL_YEARS),
            "salaries": random_bigint(5000000, 50000000),
            "maintenance": random_bigint(500000, 5000000),
            "seminars": random_bigint(100000, 1000000),
            "other_operational": random_bigint(200000, 2000000),
            "total_operational": random_bigint(10000000, 60000000),
            "institute": random.choice(IIT_NAMES)
        })
    for d in data:
        conn.execute(text("""
            INSERT INTO financial_expenses_operational
            (id, financial_year, salaries, maintenance, seminars, other_operational, total_operational, institute)
            VALUES (:id, :financial_year, :salaries, :maintenance, :seminars, :other_operational, :total_operational, :institute)
        """), d)


def seed_phd_students(conn, rows: int = 10):
    print("Seeding phd_students...")
    data = []
    for i in range(rows):
        data.append({
            "id": i + 1,
            "financial_year": random.choice(FINANCIAL_YEARS),
            "program_type": random.choice(PROGRAM_TYPES),
            "total": random_int(10, 500),
            "institute": random.choice(IIT_NAMES),
            "as_on_year": random.choice(AS_ON_YEARS)
        })
    for d in data:
        conn.execute(text("""
            INSERT INTO phd_students (id, financial_year, program_type, total, institute, as_on_year)
            VALUES (:id, :financial_year, :program_type, :total, :institute, :as_on_year)
        """), d)


def seed_sanctioned_intake(conn, rows: int = 10):
    print("Seeding sanctioned_intake...")
    data = []
    for i in range(rows):
        data.append({
            "id": i + 1,
            "program": random.choice(PROGRAM_TYPES),
            "financial_year": random.choice(FINANCIAL_YEARS),
            "seats": random_int(20, 200),
            "institute": random.choice(IIT_NAMES),
            "as_on_year": random.choice(AS_ON_YEARS)
        })
    for d in data:
        conn.execute(text("""
            INSERT INTO sanctioned_intake (id, program, financial_year, seats, institute, as_on_year)
            VALUES (:id, :program, :financial_year, :seats, :institute, :as_on_year)
        """), d)


def seed_actual_student_strength(conn, rows: int = 10):
    print("Seeding actual_student_strength...")
    data = []
    for i in range(rows):
        data.append({
            "id": i + 1,
            "program": random.choice(PROGRAM_TYPES),
            "male_students": random_int(50, 500),
            "female_students": random_int(30, 400),
            "total_students": random_int(100, 900),
            "economically_weaker_section": random_int(10, 100),
            "socially_challenged": random_int(5, 50),
            "differently_abled_students": random_int(0, 20),
            "reimbursed_students": random_int(20, 200),
            "financial_year": random.choice(FINANCIAL_YEARS),
            "institute": random.choice(IIT_NAMES),
            "as_on_year": random.choice(AS_ON_YEARS)
        })
    for d in data:
        conn.execute(text("""
            INSERT INTO actual_student_strength
            (id, program, male_students, female_students, total_students,
             economically_weaker_section, socially_challenged, differently_abled_students,
             reimbursed_students, financial_year, institute, as_on_year)
            VALUES (:id, :program, :male_students, :female_students, :total_students,
                    :economically_weaker_section, :socially_challenged, :differently_abled_students,
                    :reimbursed_students, :financial_year, :institute, :as_on_year)
        """), d)


def seed_placements_and_higher_studies(conn, rows: int = 10):
    print("Seeding placements_and_higher_studies...")
    data = []
    for i in range(rows):
        data.append({
            "id": i + 1,
            "program": random.choice(PROGRAM_TYPES),
            "year_of_intake": random.choice(FINANCIAL_YEARS),
            "students_intaken": random_int(50, 300),
            "students_placed": random_int(20, 250),
            "median_package": random_int(500000, 2500000),
            "highest_package": random_int(1000000, 5000000),
            "no_of_higher_studies": random_int(5, 50),
            "institute": random.choice(IIT_NAMES),
            "as_on_year": random.choice(AS_ON_YEARS),
            "financial_year": random.choice(FINANCIAL_YEARS),
            "students_appeared": random_int(40, 280),
            "average_package": random_int(400000, 2000000),
            "total_students": random_int(50, 300)
        })
    for d in data:
        conn.execute(text("""
            INSERT INTO placements_and_higher_studies
            (id, program, year_of_intake, students_intaken, students_placed,
             median_package, highest_package, no_of_higher_studies, institute,
             as_on_year, financial_year, students_appeared, average_package, total_students)
            VALUES (:id, :program, :year_of_intake, :students_intaken, :students_placed,
                    :median_package, :highest_package, :no_of_higher_studies, :institute,
                    :as_on_year, :financial_year, :students_appeared, :average_package, :total_students)
        """), d)


def seed_patents_details(conn, rows: int = 10):
    print("Seeding patents_details...")
    data = []
    for i in range(rows):
        data.append({
            "financial_year": random.choice(FINANCIAL_YEARS),
            "patents_published": random_int(5, 50),
            "patents_granted": random_int(2, 30),
            "patents_commercialized": random_int(1, 10),
            "institute": random.choice(IIT_NAMES),
            "as_on_year": random.choice(AS_ON_YEARS),
            "id": i + 1
        })
    for d in data:
        conn.execute(text("""
            INSERT INTO patents_details
            (financial_year, patents_published, patents_granted, patents_commercialized, institute, as_on_year, id)
            VALUES (:financial_year, :patents_published, :patents_granted, :patents_commercialized, :institute, :as_on_year, :id)
        """), d)


def seed_fdp_details(conn, rows: int = 10):
    print("Seeding fdp_details...")
    data = []
    for i in range(rows):
        data.append({
            "financial_year": random.choice(FINANCIAL_YEARS),
            "title_of_course": f"FDP Course {i+1}",
            "fdp_sponsered": random.choice(GOV_ORGS),
            "certificate_offering_department": f"Department {random.randint(1, 10)}",
            "from_date": "2024-01-15",
            "to_date": "2024-01-30",
            "duration_days": random_int(5, 30),
            "resource_person_name": f"Dr. Resource {i+1}",
            "no_of_participants": random_int(10, 100)
        })
    for d in data:
        conn.execute(text("""
            INSERT INTO fdp_details
            (financial_year, title_of_course, fdp_sponsered, certificate_offering_department,
             from_date, to_date, duration_days, resource_person_name, no_of_participants)
            VALUES (:financial_year, :title_of_course, :fdp_sponsered, :certificate_offering_department,
                    :from_date, :to_date, :duration_days, :resource_person_name, :no_of_participants)
        """), d)


def seed_faculty_details(conn, rows: int = 10):
    print("Seeding faculty_details...")
    data = []
    for i in range(rows):
        data.append({
            "num_faculties": random_int(50, 500),
            "institute": random.choice(IIT_NAMES),
            "as_on_year": random.choice(AS_ON_YEARS),
            "id": i + 1
        })
    for d in data:
        conn.execute(text("""
            INSERT INTO faculty_details (num_faculties, institute, as_on_year, id)
            VALUES (:num_faculties, :institute, :as_on_year, :id)
        """), d)


def seed_faculty_strength(conn, rows: int = 10):
    print("Seeding faculty_strength...")
    data = []
    for i in range(rows):
        data.append({
            "id": i + 1,
            "institute": random.choice(IIT_NAMES),
            "academic_year": random.choice(FINANCIAL_YEARS),
            "as_on": random.choice(AS_ON_YEARS),
            "total_male_faculty": random_int(50, 300),
            "total_female_faculty": random_int(20, 150),
            "total_male_sc": random_int(5, 30),
            "total_female_sc": random_int(3, 20),
            "total_male_st": random_int(2, 15),
            "total_female_st": random_int(1, 10),
            "total_male_obc": random_int(10, 50),
            "total_female_obc": random_int(8, 40)
        })
    for d in data:
        conn.execute(text("""
            INSERT INTO faculty_strength
            (id, institute, academic_year, as_on, total_male_faculty, total_female_faculty,
             total_male_sc, total_female_sc, total_male_st, total_female_st, total_male_obc, total_female_obc)
            VALUES (:id, :institute, :academic_year, :as_on, :total_male_faculty, :total_female_faculty,
                    :total_male_sc, :total_female_sc, :total_male_st, :total_female_st, :total_male_obc, :total_female_obc)
        """), d)


def seed_expertise(conn, rows: int = 10):
    print("Seeding expertise...")
    data = []
    for i in range(rows):
        data.append({
            "id": i + 1,
            "name": f"Dr. Expert {i+1}",
            "designation": random.choice(["Professor", "Associate Professor", "Assistant Professor"]),
            "email": f"expert{i+1}@iit.ac.in",
            "specialization": random.choice(RESEARCH_AREAS),
            "research_area": random.choice(RESEARCH_AREAS),
            "current_affiliation": random.choice(IIT_NAMES),
            "experience_years": random_int(5, 30),
            "publications_count": random_int(20, 200),
            "phone": f"+91-98765{i+1:05d}"
        })
    for d in data:
        conn.execute(text("""
            INSERT INTO expertise
            (id, name, designation, email, specialization, research_area,
             current_affiliation, experience_years, publications_count, phone)
            VALUES (:id, :name, :designation, :email, :specialization, :research_area,
                    :current_affiliation, :experience_years, :publications_count, :phone)
        """), d)


def seed_master_expertise(conn, rows: int = 10):
    print("Seeding master_expertise...")
    data = []
    for i in range(rows):
        data.append({
            "id": i + 1,
            "institute": random.choice(IIT_NAMES),
            "department": f"Department {random.randint(1, 15)}"
        })
    for d in data:
        conn.execute(text("""
            INSERT INTO master_expertise (id, institute, department)
            VALUES (:id, :institute, :department)
        """), d)


def seed_package_data(conn, rows: int = 10):
    print("Seeding package_data...")
    data = []
    for i in range(rows):
        data.append({
            "id": i + 1,
            "name": f"Package {i+1}",
            "package": f"{random_int(5, 30)} LPA",
            "status": random.choice(["Active", "Inactive", "Expired"])
        })
    for d in data:
        conn.execute(text("""
            INSERT INTO package_data (id, name, package, status)
            VALUES (:id, :name, :package, :status)
        """), d)


def seed_role_data(conn, rows: int = 10):
    print("Seeding role_data...")
    data = []
    for i in range(rows):
        data.append({
            "id": i + 1,
            "name": f"Role {i+1}",
            "status": random.choice(["Active", "Inactive"])
        })
    for d in data:
        conn.execute(text("""
            INSERT INTO role_data (id, name, status)
            VALUES (:id, :name, :status)
        """), d)


def seed_seed_funding(conn, rows: int = 10):
    print("Seeding seed_funding...")
    data = []
    for i in range(rows):
        data.append({
            "id": i + 1,
            "startup_name": f"Startup {i+1}",
            "dpiit_no": f"DPIIT{1000+i}",
            "seed_funding_received": random_bigint(100000, 5000000),
            "year_of_receiving_fund": random.choice(FINANCIAL_YEARS),
            "achievement_level": random.choice(["Level 1", "Level 2", "Level 3"]),
            "type_of_investment": random.choice(["Grant", "Equity", "Convertible Note"]),
            "institute": random.choice(IIT_NAMES),
            "as_on_year": random.choice(AS_ON_YEARS)
        })
    for d in data:
        conn.execute(text("""
            INSERT INTO seed_funding
            (id, startup_name, dpiit_no, seed_funding_received, year_of_receiving_fund,
             achievement_level, type_of_investment, institute, as_on_year)
            VALUES (:id, :startup_name, :dpiit_no, :seed_funding_received, :year_of_receiving_fund,
                    :achievement_level, :type_of_investment, :institute, :as_on_year)
        """), d)


def seed_startup_receiving_vc_investment(conn, rows: int = 10):
    print("Seeding startup_receiving_vc_investment...")
    data = []
    for i in range(rows):
        data.append({
            "startup_name": f"VC Startup {i+1}",
            "amount_received": random_bigint(1000000, 50000000),
            "organisation_name": f"VC Firm {i+1}",
            "year_of_receiving": random.choice(FINANCIAL_YEARS),
            "institute": random.choice(IIT_NAMES),
            "as_on_year": random.choice(AS_ON_YEARS),
            "id": i + 1
        })
    for d in data:
        conn.execute(text("""
            INSERT INTO startup_receiving_vc_investment
            (startup_name, amount_received, organisation_name, year_of_receiving, institute, as_on_year, id)
            VALUES (:startup_name, :amount_received, :organisation_name, :year_of_receiving, :institute, :as_on_year, :id)
        """), d)


def seed_startup_recognition(conn, rows: int = 10):
    print("Seeding startup_recognition...")
    data = []
    for i in range(rows):
        data.append({
            "startup_name": f"Recognized Startup {i+1}",
            "year_of_recognition": random.choice(FINANCIAL_YEARS),
            "registration_no": f"REG{1000+i}",
            "institute": random.choice(IIT_NAMES),
            "dpiit_no": f"DPIIT{2000+i}",
            "as_on_year": random.choice(AS_ON_YEARS)
        })
    for d in data:
        conn.execute(text("""
            INSERT INTO startup_recognition
            (startup_name, year_of_recognition, registration_no, institute, dpiit_no, as_on_year)
            VALUES (:startup_name, :year_of_recognition, :registration_no, :institute, :dpiit_no, :as_on_year)
        """), d)


def seed_startups_turnover_50_lacs(conn, rows: int = 10):
    print("Seeding startups_turnover_50_lacs...")
    data = []
    for i in range(rows):
        data.append({
            "startup_name": f"High Turnover Startup {i+1}",
            "company_turnover": random_bigint(5000000, 100000000),
            "financial_year": random.choice(FINANCIAL_YEARS),
            "institute": random.choice(IIT_NAMES),
            "as_on_year": random.choice(AS_ON_YEARS),
            "id": i + 1
        })
    for d in data:
        conn.execute(text("""
            INSERT INTO startups_turnover_50_lacs
            (startup_name, company_turnover, financial_year, institute, as_on_year, id)
            VALUES (:startup_name, :company_turnover, :financial_year, :institute, :as_on_year, :id)
        """), d)


def seed_fdi_investment(conn, rows: int = 10):
    print("Seeding fdi_investment...")
    data = []
    for i in range(rows):
        data.append({
            "startup_name": f"FDI Startup {i+1}",
            "investment_received": random_bigint(1000000, 20000000),
            "year_of_receiving": random.choice(FINANCIAL_YEARS),
            "institute": random.choice(IIT_NAMES),
            "organisation_name": f"Foreign Investor {i+1}",
            "city": random.choice(["Mumbai", "Bangalore", "Hyderabad", "Chennai", "Pune"])
        })
    for d in data:
        conn.execute(text("""
            INSERT INTO fdi_investment
            (startup_name, investment_received, year_of_receiving, institute, organisation_name, city)
            VALUES (:startup_name, :investment_received, :year_of_receiving, :institute, :organisation_name, :city)
        """), d)


def seed_founders_of_fortune_500_companies(conn, rows: int = 10):
    print("Seeding founders_of_fortune_500_companies...")
    data = []
    for i in range(rows):
        data.append({
            "name_of_alumni": f"Alumni Founder {i+1}",
            "program_passed_from": random.choice(PROGRAM_TYPES),
            "year_of_passing": f"20{random.randint(10, 24)}",
            "comapny_name": f"Fortune 500 Company {i+1}",
            "designation": random.choice(["CEO", "CTO", "CFO", "COO", "Founder"]),
            "linkedin_url": f"https://linkedin.com/in/founder{i+1}",
            "passout_year": f"20{random.randint(10, 24)}",
            "company_url": f"https://fortune500company{i+1}.com"
        })
    for d in data:
        conn.execute(text("""
            INSERT INTO founders_of_fortune_500_companies
            (name_of_alumni, program_passed_from, year_of_passing, comapny_name,
             designation, linkedin_url, passout_year, company_url)
            VALUES (:name_of_alumni, :program_passed_from, :year_of_passing, :comapny_name,
                    :designation, :linkedin_url, :passout_year, :company_url)
        """), d)


def seed_research_consultancy_details_consultancy(conn, rows: int = 10):
    print("Seeding research_consultancy_details_consultancy...")
    data = []
    for i in range(rows):
        data.append({
            "id": i + 1,
            "financial_year": random.choice(FINANCIAL_YEARS),
            "consultancy_projects": random_int(5, 50),
            "client_organisations": random_int(3, 30),
            "revenue_generated": random_bigint(1000000, 20000000),
            "institute": random.choice(IIT_NAMES),
            "as_on_year": random.choice(AS_ON_YEARS)
        })
    for d in data:
        conn.execute(text("""
            INSERT INTO research_consultancy_details_consultancy
            (id, financial_year, consultancy_projects, client_organisations, revenue_generated, institute, as_on_year)
            VALUES (:id, :financial_year, :consultancy_projects, :client_organisations, :revenue_generated, :institute, :as_on_year)
        """), d)


def seed_research_consultancy_details_sponsered(conn, rows: int = 10):
    print("Seeding research_consultancy_details_sponsered...")
    data = []
    for i in range(rows):
        data.append({
            "id": i + 1,
            "financial_year": random.choice(FINANCIAL_YEARS),
            "sponsered_projects": random_int(5, 50),
            "funding_agencies": random_int(3, 20),
            "funding_amount": random_bigint(5000000, 50000000),
            "institute": random.choice(IIT_NAMES),
            "as_on_year": random.choice(AS_ON_YEARS)
        })
    for d in data:
        conn.execute(text("""
            INSERT INTO research_consultancy_details_sponsered
            (id, financial_year, sponsered_projects, funding_agencies, funding_amount, institute, as_on_year)
            VALUES (:id, :financial_year, :sponsered_projects, :funding_agencies, :funding_amount, :institute, :as_on_year)
        """), d)


def seed_nirf_pdf_record(conn, rows: int = 10):
    print("Seeding nirf_pdf_record...")
    data = []
    for i in range(rows):
        data.append({
            "id": i + 1,
            "institute": random.choice(IIT_NAMES),
            "year": random.choice(["2023", "2024", "2025"]),
            "uploaded_by": f"admin{i+1}",
            "uploaded_at": datetime.now().isoformat(),
            "file_path": f"/data/nirf/{i+1}.pdf"
        })
    for d in data:
        conn.execute(text("""
            INSERT INTO nirf_pdf_record (id, institute, year, uploaded_by, uploaded_at, file_path)
            VALUES (:id, :institute, :year, :uploaded_by, :uploaded_at, :file_path)
        """), d)


def seed_nirf_extracted_table(conn, rows: int = 10):
    print("Seeding nirf_extracted_table...")
    data = []
    for i in range(rows):
        data.append({
            "id": i + 1,
            "pdf_record_id": random.randint(1, 10),
            "title": f"NIRF Table {i+1}",
            "header": {"columns": ["Col1", "Col2", "Col3"]},
            "row_data": {"rows": [[1, 2, 3], [4, 5, 6]]}
        })
    for d in data:
        conn.execute(text("""
            INSERT INTO nirf_extracted_table (id, pdf_record_id, title, header, row_data)
            VALUES (:id, :pdf_record_id, :title, :header, :row_data)
        """), d)


def seed_nirf_table_row(conn, rows: int = 10):
    print("Seeding nirf_table_row...")
    data = []
    for i in range(rows):
        data.append({
            "id": i + 1,
            "table_id": random.randint(1, 10),
            "data": {"row": i + 1, "value": f"Row {i+1}"}
        })
    for d in data:
        conn.execute(text("""
            INSERT INTO nirf_table_row (id, table_id, data)
            VALUES (:id, :table_id, :data)
        """), d)


def seed_tb_institute_mstr(conn, rows: int = 10):
    print("Seeding tb_institute_mstr...")
    data = []
    for i in range(rows):
        data.append({
            "id": i + 1,
            "institute_name": random.choice(IIT_NAMES + INSTITUTES),
            "short_name": f"IIT{chr(65+i)}",
            "institute_type": random.choice(["IIT", "NIT", "Deemed University", "State University"]),
            "city": random.choice(["Mumbai", "Chennai", "Delhi", "Bangalore", "Hyderabad"]),
            "state": random.choice(["Maharashtra", "Karnataka", "Tamil Nadu", "Telangana", "Gujarat"]),
            "address": f"Institution Address {i+1}",
            "established_year": random.randint(1950, 2020),
            "website_url": f"https://www.iit{i+1}.ac.in"
        })
    for d in data:
        conn.execute(text("""
            INSERT INTO tb_institute_mstr
            (id, institute_name, short_name, institute_type, city, state, address, established_year, website_url)
            VALUES (:id, :institute_name, :short_name, :institute_type, :city, :state, :address, :established_year, :website_url)
        """), d)


def seed_tb_goi_ministries_mstr(conn, rows: int = 10):
    print("Seeding tb_goi_ministries_mstr...")
    data = []
    for i in range(rows):
        data.append({
            "id": i + 1,
            "name": f"Ministry of {random.choice(['Education', 'Science', 'Health', 'Finance', 'Defense'])}",
            "short_name": f"Mo{random.randint(100, 999)}",
            "address": "Shastri Bhavan, New Delhi",
            "phone_no": f"+91-11-230{random.randint(10000, 99999)}",
            "email": f"ministry{i+1}@gov.in",
            "website": "https://www.india.gov.in"
        })
    for d in data:
        conn.execute(text("""
            INSERT INTO tb_goi_ministries_mstr
            (id, name, short_name, address, phone_no, email, website)
            VALUES (:id, :name, :short_name, :address, :phone_no, :email, :website)
        """), d)


def seed_tb_academic_year_mstr(conn, rows: int = 10):
    print("Seeding tb_academic_year_mstr...")
    data = []
    for i in range(rows):
        data.append({
            "id": i + 1,
            "year": 2020 + i,
            "academic_year": f"{2020+i}-{2021+i}"
        })
    for d in data:
        conn.execute(text("""
            INSERT INTO tb_academic_year_mstr (id, year, academic_year)
            VALUES (:id, :year, :academic_year)
        """), d)


def seed_tb_course_program_types(conn, rows: int = 10):
    print("Seeding tb_course_program_types...")
    data = []
    programs = ["B.Tech", "M.Tech", "MSc", "MBA", "PhD", "BSc", "MS", "MPhil"]
    for i, prog in enumerate(programs[:rows]):
        data.append({
            "id": i + 1,
            "program_name": prog
        })
    for d in data:
        conn.execute(text("""
            INSERT INTO tb_course_program_types (id, program_name)
            VALUES (:id, :program_name)
        """), d)


def seed_user_registration(conn, rows: int = 10):
    print("Seeding user_registration...")
    data = []
    for i in range(rows):
        data.append({
            "id": i + 1,
            "username": f"user{i+1}",
            "email": f"user{i+1}@research.ac.in",
            "password": "hashed_password_placeholder",
            "first_name": f"First{i+1}",
            "last_name": f"Last{i+1}",
            "phone_number": f"+91-98765{i+1:05d}",
            "department": f"Department {random.randint(1, 10)}",
            "institution": random.choice(IIT_NAMES),
            "is_active": True,
            "is_staff": False,
            "is_superuser": False,
            "last_login": datetime.now().isoformat(),
            "date_joined": datetime.now().isoformat(),
            "role": random.choice(["Researcher", "Government", "Industry"]),
            "tier": random.randint(1, 3),
            "approval_status": "Approved",
            "approved_by": 1,
            "approved_at": datetime.now().isoformat()
        })
    for d in data:
        conn.execute(text("""
            INSERT INTO user_registration
            (id, username, email, password, first_name, last_name, phone_number,
             department, institution, is_active, is_staff, is_superuser, last_login,
             date_joined, role, tier, approval_status, approved_by, approved_at)
            VALUES (:id, :username, :email, :password, :first_name, :last_name, :phone_number,
                    :department, :institution, :is_active, :is_staff, :is_superuser, :last_login,
                    :date_joined, :role, :tier, :approval_status, :approved_by, :approved_at)
        """), d)


def seed_advance_search_data(conn, rows: int = 10):
    print("Seeding advance_search_data...")
    data = []
    for i in range(rows):
        data.append({
            "id": i + 1,
            "title": f"Research Paper {i+1}",
            "authors": "Author 1, Author 2, Author 3",
            "guide": f"Guide {i+1}",
            "year": str(random.randint(2020, 2025)),
            "journal": f"Journal of Research {i+1}",
            "abstract": f"Abstract for paper {i+1}",
            "doi": f"10.1234/paper{i+1}"
        })
    for d in data:
        conn.execute(text("""
            INSERT INTO advance_search_data
            (id, title, authors, guide, year, journal, abstract, doi)
            VALUES (:id, :title, :authors, :guide, :year, :journal, :abstract, :doi)
        """), d)


def seed_scraped_data(conn, rows: int = 10):
    print("Seeding scraped_data...")
    data = []
    for i in range(rows):
        data.append({
            "id": i + 1,
            "title": f"Scraped Paper {i+1}",
            "authors": "Author A, Author B",
            "year": str(random.randint(2020, 2025)),
            "abstract": f"Abstract for scraped paper {i+1}",
            "doi": f"10.9999/scraped{i+1}"
        })
    for d in data:
        conn.execute(text("""
            INSERT INTO scraped_data (id, title, authors, year, abstract, doi)
            VALUES (:id, :title, :authors, :year, :abstract, :doi)
        """), d)


def seed_combined_ipo_patent_data_old(conn, rows: int = 5):
    print("Seeding combined_ipo_patent_data_old...")
    data = []
    for i in range(rows):
        data.append({
            "id": i + 1,
            "application_number": f"2020{500+i}IND",
            "title_of_invention": f"Old Patent {i+1}",
            "status": random.choice(["Granted", "Abandoned"]),
            "institute": random.choice(IIT_NAMES)
        })
    for d in data:
        conn.execute(text("""
            INSERT INTO combined_ipo_patent_data_old
            (id, application_number, title_of_invention, status, institute)
            VALUES (:id, :application_number, :title_of_invention, :status, :institute)
        """), d)


def seed_ipo_patent_details_flat(conn, rows: int = 10):
    print("Seeding ipo_patent_details_flat...")
    data = []
    for i in range(rows):
        data.append({
            "id": i + 1,
            "application_number": f"2021{2000+i}IND",
            "title_of_invention": f"IPO Patent {i+1}",
            "status": random.choice(["Granted", "Pending"]),
            "field_of_invention": random.choice(RESEARCH_AREAS),
            "institute": random.choice(IIT_NAMES),
            "financial_year": random.choice(FINANCIAL_YEARS),
            "as_on_year": random.choice(AS_ON_YEARS)
        })
    for d in data:
        conn.execute(text("""
            INSERT INTO ipo_patent_details_flat
            (id, application_number, title_of_invention, status, field_of_invention, institute, financial_year, as_on_year)
            VALUES (:id, :application_number, :title_of_invention, :status, :field_of_invention, :institute, :financial_year, :as_on_year)
        """), d)


def seed_startup_recognition_old(conn, rows: int = 5):
    print("Seeding startup_recognition_old...")
    data = []
    for i in range(rows):
        data.append({
            "startup_name": f"Old Startup {i+1}",
            "year_of_recognition": "2020-21",
            "registration_no": f"OLD{1000+i}",
            "institute": random.choice(IIT_NAMES),
            "dpiit_no": f"DPIITOLD{100+i}",
            "as_on_year": "2023-24",
            "id": i + 1
        })
    for d in data:
        conn.execute(text("""
            INSERT INTO startup_recognition_old
            (startup_name, year_of_recognition, registration_no, institute, dpiit_no, as_on_year, id)
            VALUES (:startup_name, :year_of_recognition, :registration_no, :institute, :dpiit_no, :as_on_year, :id)
        """), d)


def seed_tb_institute_scrap_data_url(conn, rows: int = 10):
    print("Seeding tb_institute_scrap_data_url...")
    data = []
    for i in range(rows):
        data.append({
            "id": i + 1,
            "institute_name": random.choice(IIT_NAMES + INSTITUTES),
            "short_name": f"SHRT{i+1}",
            "institute_type": random.choice(["IIT", "NIT", "Private"]),
            "city": random.choice(["Mumbai", "Delhi", "Chennai", "Bangalore"]),
            "state": random.choice(["Maharashtra", "Karnataka", "Tamil Nadu"]),
            "established_year": random.randint(1950, 2020),
            "address": f"Address {i+1}",
            "website_url": f"https://www.institution{i+1}.edu",
            "scrap_data_url": f"https://www.institution{i+1}.edu/data",
            "last_scraped_at": datetime.now().isoformat(),
            "scrape_status": random.choice(["Success", "Pending", "Failed"]),
            "total_records": random_int(100, 10000),
            "as_on_year": random.choice(AS_ON_YEARS)
        })
    for d in data:
        conn.execute(text("""
            INSERT INTO tb_institute_scrap_data_url
            (id, institute_name, short_name, institute_type, city, state, established_year,
             address, website_url, scrap_data_url, last_scraped_at, scrape_status, total_records, as_on_year)
            VALUES (:id, :institute_name, :short_name, :institute_type, :city, :state, :established_year,
                    :address, :website_url, :scrap_data_url, :last_scraped_at, :scrape_status, :total_records, :as_on_year)
        """), d)


def main():
    parser = argparse.ArgumentParser(description="Seed production tables with sample data")
    parser.add_argument("--url", dest="db_url", help="Database URL",
                        default=os.getenv("DATABASE_URL", "postgresql://nrg:nrg_default_password@localhost:5432/nrg"))
    parser.add_argument("--rows", type=int, default=10, help="Rows per table (default: 10)")

    args = parser.parse_args()

    print(f"Connecting to: {args.db_url}")
    engine = create_engine(args.db_url, pool_pre_ping=True)

    print(f"\nSeeding {args.rows} rows per table...")
    print("=" * 60)

    try:
        with engine.connect() as conn:
            trans = conn.begin()
            try:
                inserted = seed_all_production_tables(conn, args.rows)

                trans.commit()
                print("\n" + "=" * 60)
                print(f"All tables seeded successfully! Inserted rows: {sum(inserted.values())}")
                print("=" * 60)
                return 0
            except Exception as e:
                trans.rollback()
                print(f"\nERROR during seeding: {e}")
                return 1
    finally:
        engine.dispose()


if __name__ == "__main__":
    sys.exit(main())
