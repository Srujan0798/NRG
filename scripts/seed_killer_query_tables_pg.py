#!/usr/bin/env python3
"""
Seed the 4 killer-query PostgreSQL tables with representative data.

Run with:
    python3 scripts/seed_killer_query_tables_pg.py

Requires DATABASE_URL or falls back to docker-internal defaults.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

SQL = """
-- innovations_at_various_stages_of_technology_readiness_level
INSERT INTO innovations_at_various_stages_of_technology_readiness_level 
  (innovation_name, stage_of_technology, financial_year, institute, as_on_year)
SELECT
  'Innovation ' || i.num || ' - ' || inst.name,
  'Level ' || stage.num,
  year.yr,
  inst.name,
  split_part(year.yr, '-', 1)
FROM generate_series(1, 5) AS i(num)
CROSS JOIN (VALUES 
  ('IIT Madras'), ('IIT Bombay'), ('IIT Delhi'), 
  ('IIT Gandhinagar'), ('IIT Kanpur'), ('IIT Kharagpur'),
  ('IIT Hyderabad'), ('IIT Roorkee')
) AS inst(name)
CROSS JOIN (VALUES 
  ('2020-21'), ('2021-22'), ('2022-23'), ('2023-24')
) AS year(yr)
CROSS JOIN generate_series(1, 9) AS stage(num)
ON CONFLICT DO NOTHING;

-- innovation_grant_from_govt
INSERT INTO innovation_grant_from_govt 
  (gov_organisation_name, grant_received, year_of_receiving, institute, as_on_year)
SELECT
  agency.name,
  (random() * 90000000 + 10000000)::bigint,
  year.yr,
  inst.name,
  split_part(year.yr, '-', 1)
FROM (VALUES 
  ('DST-SERB'), ('ANRF'), ('MeitY'), ('DBT'), ('CSIR'), ('ICMR'), ('Ministry of Education')
) AS agency(name)
CROSS JOIN (VALUES 
  ('IIT Madras'), ('IIT Bombay'), ('IIT Delhi'), 
  ('IIT Gandhinagar'), ('IIT Kanpur'), ('IIT Kharagpur'),
  ('IIT Hyderabad'), ('IIT Roorkee')
) AS inst(name)
CROSS JOIN (VALUES 
  ('2019-20'), ('2020-21'), ('2021-22'), ('2022-23'), ('2023-24')
) AS year(yr)
ON CONFLICT DO NOTHING;

-- Simulate grant drops for K-Q3
UPDATE innovation_grant_from_govt
SET grant_received = (grant_received * 0.30)::bigint
WHERE year_of_receiving = '2021-22' 
  AND institute IN ('IIT Delhi', 'IIT Hyderabad');

-- combined_ipo_patent_data
INSERT INTO combined_ipo_patent_data 
  (oid, application_number, source_collection, invention_title, 
   application_filing_date, applicants, application_type, 
   date_of_grant, status, inserted_at)
SELECT
  'OID-' || inst.name || '-' || s.num || '-' || year.yr_start,
  'APP-' || inst.name || '-' || year.yr || '-' || s.num,
  'IPO',
  'Innovation Patent ' || s.num || ' from ' || inst.name,
  (year.yr_start || '-' || lpad((s.num % 12 + 1)::text, 2, '0') || '-15'),
  inst.name,
  CASE WHEN s.num % 3 = 0 THEN 'PCT' ELSE 'Regular' END,
  CASE WHEN s.num % 4 != 0 THEN (year.yr_start || '-12-15') ELSE NULL END,
  CASE WHEN s.num % 4 != 0 THEN 'Granted' ELSE 'Filed' END,
  NOW()
FROM generate_series(1, 8) AS s(num)
CROSS JOIN (VALUES 
  ('IIT Madras'), ('IIT Bombay'), ('IIT Delhi'), 
  ('IIT Gandhinagar'), ('IIT Kanpur'), ('IIT Kharagpur'),
  ('IIT Hyderabad'), ('IIT Roorkee')
) AS inst(name)
CROSS JOIN (VALUES 
  ('2020-21', '2020'), ('2021-22', '2021'), 
  ('2022-23', '2022'), ('2023-24', '2023')
) AS year(yr, yr_start)
ON CONFLICT DO NOTHING;

-- Extra patents for grant-drop institutes (doing more with less)
INSERT INTO combined_ipo_patent_data 
  (oid, application_number, source_collection, invention_title, 
   application_filing_date, applicants, application_type, 
   date_of_grant, status, inserted_at)
SELECT
  'EXTRA-' || inst.name || '-' || s.num,
  'APP-EXTRA-' || inst.name || '-2021-' || s.num,
  'IPO',
  'Extra Patent ' || s.num || ' - ' || inst.name,
  ('2021-' || lpad((s.num % 12 + 1)::text, 2, '0') || '-15'),
  inst.name, 'Regular', '2021-12-15', 'Granted', NOW()
FROM generate_series(1, 6) AS s(num)
CROSS JOIN (VALUES ('IIT Delhi'), ('IIT Hyderabad')) AS inst(name)
ON CONFLICT DO NOTHING;

-- academic_courses_details
INSERT INTO academic_courses_details 
  (financial_year, title_of_course, course_code, type_of_course, 
   level_of_course, course_offering_department, total_credit_score, 
   institute, as_on_year)
SELECT
  year.yr,
  dept.dname || ' ' || type_c.tname || ' Course ' || s.num,
  upper(substring(dept.dname, 1, 2)) || type_c.code || s.num::text,
  type_c.tname,
  type_c.level,
  dept.dname,
  (s.num % 4 + 2)::text || '.' || (s.num % 10)::text,
  inst.name,
  split_part(year.yr, '-', 1)
FROM generate_series(1, 10) AS s(num)
CROSS JOIN (VALUES 
  ('IIT Madras'), ('IIT Bombay'), ('IIT Delhi'), 
  ('IIT Gandhinagar'), ('IIT Kanpur'), ('IIT Kharagpur'),
  ('IIT Hyderabad'), ('IIT Roorkee')
) AS inst(name)
CROSS JOIN (VALUES 
  ('2020-21'), ('2021-22'), ('2022-23'), ('2023-24')
) AS year(yr)
CROSS JOIN (VALUES 
  ('AI & Machine Learning', 'PHD', 'PhD', 'PhD'),
  ('Robotics', 'UG', 'Undergraduate', 'UG'),
  ('Quantum Computing', 'PG', 'Postgraduate', 'PG'),
  ('Biotechnology', 'PG2', 'Postgraduate', 'PG')
) AS type_c(dname, code, tname, level)
CROSS JOIN (VALUES ('Computer Science'), ('Electrical Engineering'), ('Mechanical Engineering')) AS dept(dname)
ON CONFLICT DO NOTHING;
"""


def main() -> None:
    pg_user = os.getenv("POSTGRES_USER", "nrg")
    pg_pass = os.getenv("POSTGRES_PASSWORD", "nrg_default_password")
    pg_db = os.getenv("POSTGRES_DB", "nrg")
    pg_host = os.getenv("POSTGRES_HOST", "127.0.0.1")
    pg_port = os.getenv("POSTGRES_PORT", "5432")

    # Try docker exec first, then direct psql
    result = subprocess.run(
        ["docker", "exec", "-i", "nrg-postgres",
         "psql", "-U", pg_user, "-d", pg_db],
        input=SQL, capture_output=True, text=True
    )
    if result.returncode != 0:
        env = {**os.environ, "PGPASSWORD": pg_pass}
        result = subprocess.run(
            ["psql", "-U", pg_user, "-d", pg_db, "-h", pg_host, "-p", pg_port, "-c", SQL],
            capture_output=True, text=True, env=env
        )

    if result.returncode == 0:
        print("✓ Killer query tables seeded successfully")
        print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
    else:
        print(f"✗ Seed failed: {result.stderr[:500]}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
