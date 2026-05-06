-- Local PostgreSQL seed rows for the KILLER-03 live API gate.
-- These rows exercise the canonical combined_ipo_patent_data shape used by
-- the grant-drop/patent-rise query without changing application logic.

INSERT INTO public.combined_ipo_patent_data (
    application_number,
    source_collection,
    invention_title,
    application_filing_date,
    field_of_invention,
    inventors,
    applicants,
    application_type,
    status,
    patent_number,
    date_of_grant,
    legal_status,
    granted_patent_title,
    patent_grant_number,
    university_name,
    fetched_from
)
SELECT
    v.application_number,
    'nrg-local-killer-query-seed',
    v.invention_title,
    v.application_filing_date,
    v.field_of_invention,
    v.inventors,
    v.applicants,
    'Ordinary',
    'Granted',
    v.patent_number,
    v.date_of_grant,
    'Granted',
    v.invention_title,
    v.patent_grant_number,
    v.university_name,
    'db/seed/003_killer_query_patent_seed.sql'
FROM (
    VALUES
        ('KQ3-IITD-2020-001', 'Adaptive microgrid controller baseline', '2020-02-15', 'Electrical engineering', 'Dr. Neeraj Bansal', 'IIT Delhi', 'IN-KQ3-IITD-2020-001', '2020-09-15', 'KQ3-GRANT-IITD-2020-001', 'IIT Delhi'),
        ('KQ3-IITD-2021-001', 'Grid-forming microinverter control', '2021-01-10', 'Electrical engineering', 'Dr. Neeraj Bansal', 'IIT Delhi', 'IN-KQ3-IITD-2021-001', '2021-04-12', 'KQ3-GRANT-IITD-2021-001', 'IIT Delhi'),
        ('KQ3-IITD-2021-002', 'Microgrid islanding detector', '2021-03-18', 'Electrical engineering', 'Dr. Neeraj Bansal', 'IIT Delhi', 'IN-KQ3-IITD-2021-002', '2021-08-21', 'KQ3-GRANT-IITD-2021-002', 'IIT Delhi'),
        ('KQ3-IITD-2021-003', 'Power-electronics dispatch optimiser', '2021-05-02', 'Electrical engineering', 'Dr. Neeraj Bansal', 'IIT Delhi', 'IN-KQ3-IITD-2021-003', '2021-11-30', 'KQ3-GRANT-IITD-2021-003', 'IIT Delhi'),
        ('KQ3-IITH-2020-001', 'PV string fault baseline classifier', '2020-04-03', 'Renewable energy', 'Dr. Leela Iyer', 'IIT Hyderabad', 'IN-KQ3-IITH-2020-001', '2020-10-08', 'KQ3-GRANT-IITH-2020-001', 'IIT Hyderabad'),
        ('KQ3-IITH-2021-001', 'AI fault prediction for PV strings', '2021-02-12', 'Renewable energy', 'Dr. Leela Iyer', 'IIT Hyderabad', 'IN-KQ3-IITH-2021-001', '2021-05-19', 'KQ3-GRANT-IITH-2021-001', 'IIT Hyderabad'),
        ('KQ3-IITH-2021-002', 'Solar inverter predictive diagnostics', '2021-04-25', 'Renewable energy', 'Dr. Leela Iyer', 'IIT Hyderabad', 'IN-KQ3-IITH-2021-002', '2021-09-14', 'KQ3-GRANT-IITH-2021-002', 'IIT Hyderabad'),
        ('KQ3-IITH-2021-003', 'PV combiner anomaly triage', '2021-06-06', 'Renewable energy', 'Dr. Leela Iyer', 'IIT Hyderabad', 'IN-KQ3-IITH-2021-003', '2021-12-03', 'KQ3-GRANT-IITH-2021-003', 'IIT Hyderabad')
) AS v (
    application_number,
    invention_title,
    application_filing_date,
    field_of_invention,
    inventors,
    applicants,
    patent_number,
    date_of_grant,
    patent_grant_number,
    university_name
)
WHERE NOT EXISTS (
    SELECT 1
    FROM public.combined_ipo_patent_data existing
    WHERE existing.application_number = v.application_number
);
