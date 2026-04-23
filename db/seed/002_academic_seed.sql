-- NRG Academic & Innovation Data — Seed Data
-- Produces meaningful results for Dhairya's 17 Text-to-SQL benchmark queries

-- =============================================================================
-- ACADEMIC COURSES DETAILS
-- =============================================================================
INSERT INTO academic_courses_details (id, institute, title_of_course, course_code, type_of_course, level_of_course, course_offering_department, total_credit_score, financial_year, as_on_year) VALUES
-- IIT Bombay - PhD courses
('AC001', 'IIT Bombay', 'Advanced Machine Learning', 'CS601', 'Core', 'PhD', 'Computer Science', '3:1', '2021-22', '2024'),
('AC002', 'IIT Bombay', 'Quantum Computing Fundamentals', 'PH401', 'Elective', 'PhD', 'Physics', '4:0', '2021-22', '2024'),
('AC003', 'IIT Bombay', 'Deep Learning Architectures', 'CS701', 'Core', 'PhD', 'Computer Science', '3:1', '2022-23', '2024'),
('AC004', 'IIT Bombay', 'Research Methodology', 'RS500', 'Core', 'PhD', 'All Departments', '2:1', '2022-23', '2024'),
('AC005', 'IIT Bombay', 'Neural Networks', 'CS602', 'Core', 'PhD', 'Computer Science', '3:1', '2023-24', '2024'),
-- IIT Bombay - UG courses
('AC006', 'IIT Bombay', 'Introduction to Programming', 'CS101', 'Core', 'UG', 'Computer Science', '3:1', '2021-22', '2024'),
('AC007', 'IIT Bombay', 'Data Structures', 'CS102', 'Core', 'UG', 'Computer Science', '3:1', '2021-22', '2024'),
('AC008', 'IIT Bombay', 'Algorithms', 'CS201', 'Core', 'UG', 'Computer Science', '4:0', '2022-23', '2024'),
('AC009', 'IIT Bombay', 'Operating Systems', 'CS301', 'Core', 'UG', 'Computer Science', '3:1', '2022-23', '2024'),
('AC010', 'IIT Bombay', 'Computer Networks', 'CS401', 'Core', 'UG', 'Computer Science', '3:1', '2023-24', '2024'),
-- IIT Madras - PG courses
('AC011', 'IIT Madras', 'Artificial Intelligence', 'AI501', 'Core', 'PG', 'AI & Robotics', '3:1', '2021-22', '2024'),
('AC012', 'IIT Madras', 'Robotics Systems', 'RS502', 'Elective', 'PG', 'Mechanical Eng', '3:1', '2021-22', '2024'),
('AC013', 'IIT Madras', 'Computer Vision', 'CV503', 'Core', 'PG', 'Electrical Eng', '3:1', '2022-23', '2024'),
('AC014', 'IIT Madras', 'Natural Language Processing', 'NLP504', 'Core', 'PG', 'CS & AI', '3:1', '2022-23', '2024'),
('AC015', 'IIT Madras', 'Reinforcement Learning', 'RL505', 'Elective', 'PG', 'CS & AI', '3:1', '2023-24', '2024'),
-- IIT Madras - PhD courses
('AC016', 'IIT Madras', 'Advanced TRL Research', 'TR601', 'Core', 'PhD', 'Technology Innovation', '4:0', '2021-22', '2024'),
('AC017', 'IIT Madras', 'Innovation Management', 'IM602', 'Core', 'PhD', 'Management Studies', '3:1', '2022-23', '2024'),
('AC018', 'IIT Madras', 'Technology Commercialization', 'TC603', 'Elective', 'PhD', 'Management Studies', '3:0', '2023-24', '2024'),
-- IIT Madras - UG courses
('AC019', 'IIT Madras', 'Engineering Mathematics', 'MA101', 'Core', 'UG', 'Mathematics', '4:0', '2021-22', '2024'),
('AC020', 'IIT Madras', 'Physics for Engineers', 'PH102', 'Core', 'UG', 'Physics', '3:1', '2021-22', '2024'),
('AC021', 'IIT Madras', 'Innovation Workshop', 'IW201', 'Core', 'UG', 'Innovation Center', '2:1', '2022-23', '2024'),
-- IIT Delhi - PhD courses
('AC022', 'IIT Delhi', 'Sustainable Energy Systems', 'SE601', 'Core', 'PhD', 'Energy Science', '3:1', '2021-22', '2024'),
('AC023', 'IIT Delhi', 'Climate Technology', 'CT602', 'Elective', 'PhD', 'Environmental Eng', '3:1', '2022-23', '2024'),
-- IIT Hyderabad - courses
('AC024', 'IIT Hyderabad', 'AI for Healthcare', 'AI501', 'Core', 'PG', 'AI', '3:1', '2021-22', '2024'),
('AC025', 'IIT Hyderabad', 'Embedded Systems', 'ES401', 'Core', 'UG', 'ECE', '3:1', '2022-23', '2024'),
('AC026', 'IIT Hyderabad', 'VLSI Design', 'VL501', 'Core', 'PG', 'ECE', '4:0', '2023-24', '2024'),
-- NIT Karnataka - courses
('AC027', 'NIT Karnataka', 'Software Engineering', 'SE301', 'Core', 'UG', 'CS & IT', '3:1', '2022-23', '2024'),
('AC028', 'NIT Karnataka', 'Machine Learning', 'ML401', 'Elective', 'PG', 'CS & IT', '3:1', '2023-24', '2024');

-- =============================================================================
-- INNOVATION GRANTS FROM GOVT
-- =============================================================================
INSERT INTO innovation_grant_from_govt (id, institute, gov_organisation_name, grant_received, year_of_receiving, as_on_year) VALUES
-- IIT Bombay grants by year
('IG001', 'IIT Bombay', 'DST-SERB', 15000000, '2020-21', '2024'),
('IG002', 'IIT Bombay', 'DST-SERB', 16000000, '2021-22', '2024'),
('IG003', 'IIT Bombay', 'DST-SERB', 8000000, '2022-23', '2024'),  -- >50% drop
('IG004', 'IIT Bombay', 'DRDO', 25000000, '2021-22', '2024'),
('IG005', 'IIT Bombay', 'DRDO', 26000000, '2022-23', '2024'),
('IG006', 'IIT Bombay', 'DBT', 12000000, '2022-23', '2024'),
-- IIT Madras grants by year
('IG007', 'IIT Madras', 'DST-SERB', 20000000, '2020-21', '2024'),
('IG008', 'IIT Madras', 'DST-SERB', 22000000, '2021-22', '2024'),
('IG009', 'IIT Madras', 'DST-SERB', 25000000, '2022-23', '2024'),  -- Growing
('IG010', 'IIT Madras', 'DRDO', 18000000, '2021-22', '2024'),
('IG011', 'IIT Madras', 'DRDO', 20000000, '2022-23', '2024'),
('IG012', 'IIT Madras', 'DBT', 10000000, '2022-23', '2024'),
('IG013', 'IIT Madras', 'MeitY', 15000000, '2022-23', '2024'),
-- IIT Delhi grants
('IG014', 'IIT Delhi', 'DST-SERB', 10000000, '2020-21', '2024'),
('IG015', 'IIT Delhi', 'DST-SERB', 12000000, '2021-22', '2024'),
('IG016', 'IIT Delhi', 'DST-SERB', 8000000, '2022-23', '2024'),
-- NIT Karnataka grants
('IG017', 'NIT Karnataka', 'DST-SERB', 5000000, '2020-21', '2024'),
('IG018', 'NIT Karnataka', 'DST-SERB', 5500000, '2021-22', '2024'),
('IG019', 'NIT Karnataka', 'DST-SERB', 6000000, '2022-23', '2024'),
-- Multiple agencies for Q4 (top 5 by amount)
('IG020', 'IIT Bombay', 'DST-SERB', 8000000, '2022-23', '2024'),
('IG021', 'IIT Madras', 'DRDO', 20000000, '2022-23', '2024'),
('IG022', 'IIT Delhi', 'DRDO', 15000000, '2022-23', '2024'),
('IG023', 'NIT Karnataka', 'AICTE', 3000000, '2022-23', '2024'),
('IG024', 'IIT Hyderabad', 'DST-SERB', 7000000, '2022-23', '2024');

-- =============================================================================
-- INNOVATIONS AT VARIOUS STAGES OF TECHNOLOGY READINESS LEVEL
-- =============================================================================
INSERT INTO innovations_at_various_stages_of_technology_readiness_level (id, institute, innovation_name, stage_of_technology, financial_year) VALUES
-- IIT Madras TRL pipeline (for Q5, Q6, Q17)
('TRL001', 'IIT Madras', 'AI-Powered Cancer Diagnostic', 'Level 4', '2021-22'),  -- Lab Validation
('TRL002', 'IIT Madras', 'AI-Powered Cancer Diagnostic', 'Level 4', '2022-23'),  -- Lab Validation
('TRL003', 'IIT Madras', 'Smart Grid Controller', 'Level 6', '2021-22'),  -- Pilot Scale
('TRL004', 'IIT Madras', 'Smart Grid Controller', 'Level 7', '2022-23'),  -- Pre-Pilot
('TRL005', 'IIT Madras', 'Smart Grid Controller', 'Level 8', '2023-24'),  -- First-of-Kind
('TRL006', 'IIT Madras', 'Quantum Key Distribution', 'Level 3', '2021-22'),  -- Feasibility
('TRL007', 'IIT Madras', 'Quantum Key Distribution', 'Level 5', '2022-23'),  -- Tech Demo
('TRL008', 'IIT Madras', 'Autonomous Drone Platform', 'Level 9', '2022-23'),  -- Market Ready (Q6)
('TRL009', 'IIT Madras', 'Battery Management System', 'Level 5', '2021-22'),
('TRL010', 'IIT Madras', 'Battery Management System', 'Level 7', '2022-23'),
-- IIT Bombay TRL pipeline
('TRL011', 'IIT Bombay', 'Medical Imaging AI', 'Level 4', '2021-22'),
('TRL012', 'IIT Bombay', 'Medical Imaging AI', 'Level 6', '2022-23'),
('TRL013', 'IIT Bombay', 'Medical Imaging AI', 'Level 8', '2023-24'),
('TRL014', 'IIT Bombay', 'NLP for Vernacular Languages', 'Level 5', '2021-22'),
('TRL015', 'IIT Bombay', 'NLP for Vernacular Languages', 'Level 7', '2022-23'),
-- IIT Delhi TRL
('TRL016', 'IIT Delhi', 'Hydrogen Fuel Cell', 'Level 3', '2021-22'),
('TRL017', 'IIT Delhi', 'Hydrogen Fuel Cell', 'Level 5', '2022-23'),
('TRL018', 'IIT Delhi', 'Hydrogen Fuel Cell', 'Level 6', '2023-24');

-- =============================================================================
-- COMBINED IPO PATENT DATA
-- =============================================================================
INSERT INTO combined_ipo_patent_data (id, institute, applicants, title, status, filing_date, grant_date, financial_year) VALUES
('PAT001', 'IIT Madras', 'IIT Madras', 'AI Cancer Diagnostic Algorithm', 'Granted', '2020-03-15', '2023-06-20', '2022-23'),
('PAT002', 'IIT Madras', 'IIT Madras', 'Quantum Encryption Method', 'Granted', '2021-01-10', '2023-09-15', '2022-23'),
('PAT003', 'IIT Madras', 'IIT Madras', 'Battery Management System', 'Granted', '2019-07-22', '2022-12-01', '2022-23'),
('PAT004', 'IIT Madras', 'IIT Madras', 'Autonomous Drone Navigation', 'Filed', '2022-05-18', NULL, '2023-24'),
('PAT005', 'IIT Bombay', 'IIT Bombay', 'Medical Imaging Processing', 'Granted', '2020-08-14', '2023-03-10', '2022-23'),
('PAT006', 'IIT Bombay', 'IIT Bombay', 'NLP Vernacular Translation', 'Granted', '2021-02-28', '2023-11-22', '2022-23'),
('PAT007', 'IIT Bombay', 'IIT Bombay', 'Smart Grid Optimization', 'Examined', '2022-01-05', NULL, '2023-24'),
('PAT008', 'IIT Delhi', 'IIT Delhi', 'Hydrogen Storage Technology', 'Filed', '2022-06-30', NULL, '2023-24'),
('PAT009', 'IIT Hyderabad', 'IIT Hyderabad', 'Healthcare AI Triage', 'Granted', '2020-11-12', '2023-07-18', '2022-23'),
('PAT010', 'NIT Karnataka', 'NIT Karnataka', 'Agriculture Drone System', 'Granted', '2019-04-20', '2022-08-05', '2021-22');

-- =============================================================================
-- FINANCIAL EXPENSES - CAPITAL
-- =============================================================================
INSERT INTO financial_expenses_capital (id, institute, financial_year, library, equipment, workshops, capital_assets) VALUES
-- IIT Madras - high capex (for Q14 gap analysis)
('CE001', 'IIT Madras', '2023-24', 5000000, 25000000, 3000000, 40000000),  -- High capex
('CE002', 'IIT Bombay', '2023-24', 3000000, 15000000, 2000000, 20000000),
('CE003', 'IIT Delhi', '2023-24', 2000000, 10000000, 1500000, 12000000),
('CE004', 'NIT Karnataka', '2023-24', 1000000, 5000000, 500000, 3000000),
('CE005', 'IIT Hyderabad', '2023-24', 1500000, 8000000, 1000000, 8000000),
-- Previous years for trend
('CE006', 'IIT Madras', '2022-23', 4000000, 20000000, 2500000, 35000000),
('CE007', 'IIT Madras', '2021-22', 3500000, 18000000, 2000000, 30000000);

-- =============================================================================
-- FINANCIAL EXPENSES - OPERATIONAL
-- =============================================================================
INSERT INTO financial_expenses_operational (id, institute, as_on_year, salaries, maintenance, seminars) VALUES
-- IIT Madras - operational expenses (for Q16 utilization audit)
('OE001', 'IIT Madras', '2023', 200000000, 15000000, 5000000),
('OE002', 'IIT Bombay', '2023', 250000000, 20000000, 8000000),
('OE003', 'IIT Delhi', '2023', 150000000, 10000000, 4000000),
('OE004', 'NIT Karnataka', '2023', 80000000, 5000000, 2000000),
-- Different year for Q16
('OE005', 'IIT Madras', '2022', 180000000, 12000000, 4000000),
('OE006', 'IIT Bombay', '2022', 220000000, 18000000, 6000000);

-- =============================================================================
-- INCUBATION DETAILS
-- =============================================================================
INSERT INTO incubation_details (id, institute, startup_name, cohort_year, sector, status) VALUES
('INC001', 'IIT Madras', 'HealthAI Solutions', '2022', 'Healthcare AI', 'Active'),
('INC002', 'IIT Madras', 'Green Energy Systems', '2022', 'Clean Tech', 'Active'),
('INC003', 'IIT Madras', 'EduTech Platform', '2021', 'Education', 'Graduated'),
('INC004', 'IIT Bombay', 'FinTech Innovations', '2022', 'Finance', 'Active'),
('INC005', 'IIT Bombay', 'AgriDrone Technologies', '2022', 'Agriculture', 'Active'),
('INC006', 'IIT Delhi', 'CleanWater Tech', '2023', 'Water Tech', 'Active'),
('INC007', 'NIT Karnataka', 'Edison E-Vehicles', '2022', 'EV', 'Active'),
('INC008', 'IIT Hyderabad', 'BioSense Devices', '2023', 'MedTech', 'Active');

-- =============================================================================
-- STARTUP RECOGNITION
-- =============================================================================
INSERT INTO startup_recognition (id, institute, startup_name, recognition_body, recognition_year, sector) VALUES
('SR001', 'IIT Madras', 'HealthAI Solutions', 'DST-TBI', '2023', 'Healthcare AI'),
('SR002', 'IIT Madras', 'Green Energy Systems', 'DST-TBI', '2023', 'Clean Tech'),
('SR003', 'IIT Bombay', 'FinTech Innovations', 'DST-TBI', '2023', 'Finance'),
('SR004', 'IIT Delhi', 'CleanWater Tech', 'DST-TBI', '2024', 'Water Tech');

-- =============================================================================
-- PhD STUDENTS
-- =============================================================================
INSERT INTO phd_students (id, institute, department, financial_year, total, male, female) VALUES
('PHD001', 'IIT Madras', 'CS & AI', '2021-22', 120, 85, 35),
('PHD002', 'IIT Madras', 'CS & AI', '2022-23', 140, 95, 45),  -- Spiked
('PHD003', 'IIT Madras', 'Mechanical Eng', '2021-22', 80, 60, 20),
('PHD004', 'IIT Madras', 'Mechanical Eng', '2022-23', 75, 55, 20),
('PHD005', 'IIT Bombay', 'CS', '2021-22', 100, 70, 30),
('PHD006', 'IIT Bombay', 'CS', '2022-23', 110, 75, 35),
('PHD007', 'IIT Delhi', 'Energy', '2021-22', 60, 40, 20),
('PHD008', 'IIT Delhi', 'Energy', '2022-23', 65, 42, 23);

-- =============================================================================
-- SANCTIONED INTAKE
-- =============================================================================
INSERT INTO sanctioned_intake (id, institute, program, financial_year, seats) VALUES
('SI001', 'IIT Madras', 'UG', '2021-22', 500),
('SI002', 'IIT Madras', 'UG', '2022-23', 480),  -- Slightly reduced
('SI003', 'IIT Madras', 'PG', '2021-22', 300),
('SI004', 'IIT Madras', 'PG', '2022-23', 320),
('SI005', 'IIT Bombay', 'UG', '2021-22', 600),
('SI006', 'IIT Bombay', 'UG', '2022-23', 580),
('SI007', 'IIT Bombay', 'PG', '2021-22', 400),
('SI008', 'IIT Bombay', 'PG', '2022-23', 420);
