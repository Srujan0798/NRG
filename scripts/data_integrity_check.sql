-- E2: Data Integrity Validation Queries
-- READ-ONLY diagnostic queries - run against production database with replica account
-- These queries identify data quality issues for cleanup

-- ============================================================================
-- ORPHAN DETECTION QUERIES
-- Find records referencing non-existent parent records
-- ============================================================================

-- Orphan funding_records (researcher_id not in researchers)
SELECT 'funding_records -> researchers' AS orphan_check, COUNT(*) AS orphan_count
FROM funding_records f
WHERE f.researcher_id IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM researchers r WHERE r.researcher_id = f.researcher_id);

-- Orphan funding_records (institution_id not in institutions)
SELECT 'funding_records -> institutions' AS orphan_check, COUNT(*) AS orphan_count
FROM funding_records f
WHERE f.institution_id IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM institutions i WHERE i.institution_id = f.institution_id);

-- Orphan funding_records (project_id not in projects)
SELECT 'funding_records -> projects' AS orphan_check, COUNT(*) AS orphan_count
FROM funding_records f
WHERE f.project_id IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM projects p WHERE p.project_id = f.project_id);

-- Orphan patents (applicant_institution not in institutions)
SELECT 'patents -> institutions' AS orphan_check, COUNT(*) AS orphan_count
FROM patents p
WHERE p.applicant_institution IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM institutions i WHERE i.institution_id = p.applicant_institution);

-- Orphan researchers (institution_id not in institutions)
SELECT 'researchers -> institutions' AS orphan_check, COUNT(*) AS orphan_count
FROM researchers r
WHERE r.institution_id IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM institutions i WHERE i.institution_id = r.institution_id);

-- Orphan labs (institution_id not in institutions)
SELECT 'labs -> institutions' AS orphan_check, COUNT(*) AS orphan_count
FROM labs l
WHERE l.institution_id IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM institutions i WHERE i.institution_id = l.institution_id);

-- Orphan labs (director_researcher_id not in researchers)
SELECT 'labs -> researchers (director)' AS orphan_check, COUNT(*) AS orphan_count
FROM labs l
WHERE l.director_researcher_id IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM researchers r WHERE r.researcher_id = l.director_researcher_id);

-- Orphan projects (principal_investigator_id not in researchers)
SELECT 'projects -> researchers (PI)' AS orphan_check, COUNT(*) AS orphan_count
FROM projects p
WHERE p.principal_investigator_id IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM researchers r WHERE r.researcher_id = p.principal_investigator_id);

-- Orphan researcher_publications (publication_id not in publications)
SELECT 'researcher_publications -> publications' AS orphan_check, COUNT(*) AS orphan_count
FROM researcher_publications rp
WHERE NOT EXISTS (SELECT 1 FROM publications pub WHERE pub.publication_id = rp.publication_id);

-- Orphan researcher_publications (researcher_id not in researchers)
SELECT 'researcher_publications -> researchers' AS orphan_check, COUNT(*) AS orphan_count
FROM researcher_publications rp
WHERE NOT EXISTS (SELECT 1 FROM researchers r WHERE r.researcher_id = rp.researcher_id);

-- Orphan researcher_labs (lab_id not in labs)
SELECT 'researcher_labs -> labs' AS orphan_check, COUNT(*) AS orphan_count
FROM researcher_labs rl
WHERE NOT EXISTS (SELECT 1 FROM labs l WHERE l.lab_id = rl.lab_id);

-- Orphan researcher_labs (researcher_id not in researchers)
SELECT 'researcher_labs -> researchers' AS orphan_check, COUNT(*) AS orphan_count
FROM researcher_labs rl
WHERE NOT EXISTS (SELECT 1 FROM researchers r WHERE r.researcher_id = rl.researcher_id);

-- Orphan publication_keywords (publication_id not in publications)
SELECT 'publication_keywords -> publications' AS orphan_check, COUNT(*) AS orphan_count
FROM publication_keywords pk
WHERE NOT EXISTS (SELECT 1 FROM publications pub WHERE pub.publication_id = pk.publication_id);

-- Orphan publication_keywords (keyword_id not in keywords)
SELECT 'publication_keywords -> keywords' AS orphan_check, COUNT(*) AS orphan_count
FROM publication_keywords pk
WHERE NOT EXISTS (SELECT 1 FROM keywords k WHERE k.keyword_id = pk.keyword_id);

-- Detailed orphan records (sample of each type)
SELECT 'funding_records.detail' AS query_name,
       f.funding_id, f.researcher_id, f.institution_id, f.project_id
FROM funding_records f
WHERE f.researcher_id IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM researchers r WHERE r.researcher_id = f.researcher_id)
LIMIT 20;

SELECT 'patents.detail' AS query_name,
       p.patent_id, p.title, p.applicant_institution
FROM patents p
WHERE p.applicant_institution IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM institutions i WHERE i.institution_id = p.applicant_institution)
LIMIT 20;

SELECT 'researchers.detail' AS query_name,
       r.researcher_id, r.name, r.institution_id
FROM researchers r
WHERE r.institution_id IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM institutions i WHERE i.institution_id = r.institution_id)
LIMIT 20;

-- ============================================================================
-- ID NAMESPACE VALIDATION
-- Find mixed ID formats (RES_ vs RES- vs other patterns)
-- ============================================================================

-- Researcher ID format distribution
SELECT 'researcher_id_format' AS check_name,
       CASE
         WHEN researcher_id LIKE 'RES-%' THEN 'RES-dash'
         WHEN researcher_id LIKE 'RES\_%' ESCAPE '\' THEN 'RES_underscore'
         WHEN researcher_id ~ '^[A-Z]{2,3}-[0-9]+$' THEN 'GOV-format'
         WHEN researcher_id ~ '^[0-9]+$' THEN 'numeric-only'
         ELSE 'other'
       END AS format,
       COUNT(*) AS count
FROM researchers
GROUP BY 2
ORDER BY count DESC;

-- Researcher IDs with mixed formats (sample)
SELECT 'mixed_researcher_ids' AS query_name,
       researcher_id, name
FROM researchers
WHERE researcher_id LIKE '%_%'
   OR researcher_id LIKE '%-%'
LIMIT 50;

-- Validate RES_ prefix consistency (should be RES_ or RES- not both patterns)
SELECT 'inconsistent_researcher_id_formats' AS query_name,
       researcher_id
FROM researchers
WHERE researcher_id ~ 'RES_[0-9]'
  AND researcher_id ~ 'RES-[0-9]'
LIMIT 20;

-- ============================================================================
-- DATA QUALITY CHECKS
-- ============================================================================

-- Publications with invalid years (before 1900 or after current year + 1)
SELECT 'invalid_publication_years' AS check_name, COUNT(*) AS count
FROM publications
WHERE year IS NOT NULL
  AND (year < 1900 OR year > EXTRACT(YEAR FROM CURRENT_DATE) + 1);

-- Funding records with negative or zero amounts
SELECT 'invalid_funding_amounts' AS check_name, COUNT(*) AS count
FROM funding_records
WHERE amount IS NOT NULL AND amount <= 0;

-- Research documents with invalid publication years
SELECT 'invalid_doc_years' AS check_name, COUNT(*) AS count
FROM research_documents
WHERE publication_year IS NOT NULL
  AND (publication_year < 1900 OR publication_year > EXTRACT(YEAR FROM CURRENT_DATE) + 1);

-- Institutions with invalid founded years
SELECT 'invalid_institution_years' AS check_name, COUNT(*) AS count
FROM institutions
WHERE founded_year IS NOT NULL
  AND (founded_year < 1500 OR founded_year > EXTRACT(YEAR FROM CURRENT_DATE) + 1);

-- Labs with invalid established years
SELECT 'invalid_lab_years' AS check_name, COUNT(*) AS count
FROM labs
WHERE established_year IS NOT NULL
  AND (established_year < 1900 OR established_year > EXTRACT(YEAR FROM CURRENT_DATE) + 1);

-- State normalization check (all states should be standard Indian state codes)
SELECT 'non_standard_states' AS check_name, state, COUNT(*) AS count
FROM researchers
WHERE state NOT IN (
    'AP', 'AR', 'AS', 'BR', 'CH', 'CT', 'DL', 'DN', 'GA', 'GJ', 'HP', 'HR', 'JH',
    'JK', 'KA', 'KL', 'LA', 'LD', 'MH', 'ML', 'MN', 'MP', 'MZ', 'NL', 'OD', 'PB',
    'PY', 'RJ', 'SK', 'TG', 'TN', 'TR', 'TS', 'UP', 'UT', 'WB'
)
GROUP BY state
ORDER BY count DESC;
