-- NRG Academic & Innovation Data Schema
-- Tables required for Dhairya's Text-to-SQL benchmark queries
-- These tables supplement the existing NRG schema

-- =============================================================================
-- ACADEMIC COURSES
-- =============================================================================
CREATE TABLE IF NOT EXISTS academic_courses_details (
    id TEXT PRIMARY KEY,
    institute TEXT NOT NULL,
    title_of_course TEXT,
    course_code TEXT,
    type_of_course TEXT,  -- Core, Elective, Audit
    level_of_course TEXT NOT NULL,  -- UG, PG, PhD, Diploma
    course_offering_department TEXT,
    total_credit_score TEXT,  -- Format "L:T" where L=lecture, T=tutorial, e.g. "3:1"
    financial_year TEXT NOT NULL,  -- '2021-22', '2022-23', '2023-24'
    as_on_year TEXT,
    access_tier INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_academic_institute ON academic_courses_details(institute);
CREATE INDEX IF NOT EXISTS idx_academic_level ON academic_courses_details(level_of_course);
CREATE INDEX IF NOT EXISTS idx_academic_year ON academic_courses_details(financial_year);
CREATE INDEX IF NOT EXISTS idx_academic_dept ON academic_courses_details(course_offering_department);

-- =============================================================================
-- INNOVATION GRANTS FROM GOVT
-- =============================================================================
CREATE TABLE IF NOT EXISTS innovation_grant_from_govt (
    id TEXT PRIMARY KEY,
    institute TEXT NOT NULL,
    gov_organisation_name TEXT NOT NULL,
    grant_received REAL NOT NULL,
    year_of_receiving TEXT NOT NULL,  -- '2020-21', '2021-22', '2022-23'
    as_on_year TEXT,
    scheme_name TEXT,
    access_tier INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_grant_institute ON innovation_grant_from_govt(institute);
CREATE INDEX IF NOT EXISTS idx_grant_org ON innovation_grant_from_govt(gov_organisation_name);
CREATE INDEX IF NOT EXISTS idx_grant_year ON innovation_grant_from_govt(year_of_receiving);

-- =============================================================================
-- TECHNOLOGY READINESS LEVEL (TRL) PIPELINE
-- =============================================================================
CREATE TABLE IF NOT EXISTS innovations_at_various_stages_of_technology_readiness_level (
    id TEXT PRIMARY KEY,
    institute TEXT NOT NULL,
    innovation_name TEXT NOT NULL,
    stage_of_technology TEXT NOT NULL,  -- 'Level 1' through 'Level 9', NOT 'TRL 9'
    financial_year TEXT,
    as_on_year TEXT,
    technology_domain TEXT,
    access_tier INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_trl_institute ON innovations_at_various_stages_of_technology_readiness_level(institute);
CREATE INDEX IF NOT EXISTS idx_trl_stage ON innovations_at_various_stages_of_technology_readiness_level(stage_of_technology);
CREATE INDEX IF NOT EXISTS idx_trl_year ON innovations_at_various_stages_of_technology_readiness_level(financial_year);

-- =============================================================================
-- COMBINED IPO PATENT DATA
-- =============================================================================
CREATE TABLE IF NOT EXISTS combined_ipo_patent_data (
    id TEXT PRIMARY KEY,
    institute TEXT NOT NULL,
    applicants TEXT,  -- Institute name (NOT researcher IDs)
    title TEXT,
    application_number TEXT,
    status TEXT NOT NULL,  -- 'Granted', 'Filed', 'Examined', 'Rejected'
    filing_date TEXT,
    grant_date TEXT,
    financial_year TEXT,
    access_tier INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_patent_institute ON combined_ipo_patent_data(institute);
CREATE INDEX IF NOT EXISTS idx_patent_status ON combined_ipo_patent_data(status);
CREATE INDEX IF NOT EXISTS idx_patent_year ON combined_ipo_patent_data(financial_year);

-- =============================================================================
-- FINANCIAL EXPENSES - CAPITAL
-- =============================================================================
CREATE TABLE IF NOT EXISTS financial_expenses_capital (
    id TEXT PRIMARY KEY,
    institute TEXT NOT NULL,
    financial_year TEXT NOT NULL,
    as_on_year TEXT,
    library REAL DEFAULT 0,
    equipment REAL DEFAULT 0,
    workshops REAL DEFAULT 0,
    capital_assets REAL DEFAULT 0,
    other_capital REAL DEFAULT 0,
    access_tier INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_capex_institute ON financial_expenses_capital(institute);
CREATE INDEX IF NOT EXISTS idx_capex_year ON financial_expenses_capital(financial_year);

-- =============================================================================
-- FINANCIAL EXPENSES - OPERATIONAL
-- =============================================================================
CREATE TABLE IF NOT EXISTS financial_expenses_operational (
    id TEXT PRIMARY KEY,
    institute TEXT NOT NULL,
    as_on_year TEXT NOT NULL,
    salaries REAL DEFAULT 0,
    maintenance REAL DEFAULT 0,
    seminars REAL DEFAULT 0,
    consumables REAL DEFAULT 0,
    travel REAL DEFAULT 0,
    other_ops REAL DEFAULT 0,
    access_tier INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_opex_institute ON financial_expenses_operational(institute);
CREATE INDEX IF NOT EXISTS idx_opex_year ON financial_expenses_operational(as_on_year);

-- =============================================================================
-- INCUBATION DETAILS
-- =============================================================================
CREATE TABLE IF NOT EXISTS incubation_details (
    id TEXT PRIMARY KEY,
    institute TEXT NOT NULL,
    startup_name TEXT,
    cohort_year TEXT,
    sector TEXT,
    status TEXT,  -- 'Active', 'Graduated', 'Failed'
    admission_date TEXT,
    access_tier INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_incubate_institute ON incubation_details(institute);
CREATE INDEX IF NOT EXISTS idx_incubate_status ON incubation_details(status);

-- =============================================================================
-- STARTUP RECOGNITION
-- =============================================================================
CREATE TABLE IF NOT EXISTS startup_recognition (
    id TEXT PRIMARY KEY,
    institute TEXT NOT NULL,
    startup_name TEXT,
    recognition_body TEXT,
    recognition_year TEXT,
    sector TEXT,
    access_tier INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_startup_institute ON startup_recognition(institute);

-- =============================================================================
-- PhD STUDENTS
-- =============================================================================
CREATE TABLE IF NOT EXISTS phd_students (
    id TEXT PRIMARY KEY,
    institute TEXT NOT NULL,
    department TEXT,
    financial_year TEXT NOT NULL,
    total INTEGER DEFAULT 0,
    male INTEGER DEFAULT 0,
    female INTEGER DEFAULT 0,
    sc_students INTEGER DEFAULT 0,
    access_tier INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_phd_institute ON phd_students(institute);
CREATE INDEX IF NOT EXISTS idx_phd_year ON phd_students(financial_year);

-- =============================================================================
-- SANCTIONED INTAKE
-- =============================================================================
CREATE TABLE IF NOT EXISTS sanctioned_intake (
    id TEXT PRIMARY KEY,
    institute TEXT NOT NULL,
    program TEXT NOT NULL,  -- UG, PG, PhD
    financial_year TEXT NOT NULL,
    seats INTEGER DEFAULT 0,
    access_tier INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_intake_institute ON sanctioned_intake(institute);
CREATE INDEX IF NOT EXISTS idx_intake_year ON sanctioned_intake(financial_year);
CREATE INDEX IF NOT EXISTS idx_intake_program ON sanctioned_intake(program);

-- =============================================================================
-- ACTUAL STUDENT STRENGTH
-- =============================================================================
CREATE TABLE IF NOT EXISTS actual_student_strength (
    id TEXT PRIMARY KEY,
    institute TEXT NOT NULL,
    program TEXT NOT NULL,  -- UG, PG, PhD
    financial_year TEXT NOT NULL,
    male_students INTEGER DEFAULT 0,
    female_students INTEGER DEFAULT 0,
    total_students INTEGER DEFAULT 0,
    within_state INTEGER DEFAULT 0,
    outside_state INTEGER DEFAULT 0,
    outside_country INTEGER DEFAULT 0,
    economically_backward INTEGER DEFAULT 0,
    socially_challenged INTEGER DEFAULT 0,
    reimbursed_by_government INTEGER DEFAULT 0,
    reimbursed_by_institution INTEGER DEFAULT 0,
    reimbursed_by_private INTEGER DEFAULT 0,
    not_reimbursed INTEGER DEFAULT 0,
    access_tier INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_strength_institute ON actual_student_strength(institute);
CREATE INDEX IF NOT EXISTS idx_strength_program ON actual_student_strength(program);
CREATE INDEX IF NOT EXISTS idx_strength_year ON actual_student_strength(financial_year);
