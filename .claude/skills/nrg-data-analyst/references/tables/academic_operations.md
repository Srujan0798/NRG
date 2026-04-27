# Academic Operations Tables

This document contains tables for academic courses, student enrollment, financial expenses, and capacity planning.

---

## Quick Reference

### Business Context
These tables capture the operational side of academic institutions: course offerings, student admissions, PhD enrollment, and financial expenditures. Used for institutional benchmarking and capacity analysis.

### Standard Filters
```sql
-- Focus on recent data
WHERE financial_year >= '2020-21'

-- Exclude incomplete records
AND institute IS NOT NULL
```

---

## Key Tables

### academic_courses_details
**Location**: `public.academic_courses_details`
**Description**: Course offerings by institution and department.
**Primary Key**: `id` (TEXT)
**Update Frequency**: Annual (1-3 month lag)

| Column | Type | Description | Notes |
|--------|------|-------------|-------|
| **id** | TEXT | Unique identifier | |
| **institute** | TEXT | Institution name | |
| **course_offering_department** | TEXT | Department | |
| **course_name** | TEXT | Course title | |
| **level_of_course** | TEXT | UG/PG/PhD | |
| **financial_year** | TEXT | FY | |
| **access_tier** | INTEGER | Visibility | DEFAULT 1 |
| **created_at** | TEXT | Timestamp | |

**Indexes**: `idx_academic_institute`, `idx_academic_level`, `idx_academic_year`, `idx_academic_dept`

**Sample Queries**:
```sql
-- Course diversity by institute
SELECT institute, COUNT(DISTINCT course_name) AS unique_courses
FROM academic_courses_details
WHERE financial_year = '2022-23'
GROUP BY institute
ORDER BY unique_courses DESC;

-- Department-wise course count
SELECT course_offering_department, COUNT(*) AS course_count
FROM academic_courses_details
GROUP BY course_offering_department
ORDER BY course_count DESC;
```

---

### sanctioned_intake
**Location**: `public.sanctioned_intake`
**Description**: Approved student capacity by program.
**Primary Key**: `id` (TEXT)
**Update Frequency**: Annual

| Column | Type | Description | Notes |
|--------|------|-------------|-------|
| **id** | TEXT | Unique identifier | |
| **institute** | TEXT | Institution name | |
| **program** | TEXT | Program name | e.g., 'B.Tech', 'M.Tech', 'PhD' |
| **intake** | INTEGER | Approved seats | |
| **financial_year** | TEXT | FY | |
| **access_tier** | INTEGER | Visibility | DEFAULT 1 |
| **created_at** | TEXT | Timestamp | |

**Indexes**: `idx_intake_institute`, `idx_intake_year`, `idx_intake_program`

---

### actual_student_strength
**Location**: `public.actual_student_strength`
**Description**: Actual enrolled students by program.
**Primary Key**: `id` (TEXT)
**Update Frequency**: Annual

| Column | Type | Description | Notes |
|--------|------|-------------|-------|
| **id** | TEXT | Unique identifier | |
| **institute** | TEXT | Institution name | |
| **program** | TEXT | Program name | |
| **total_students** | INTEGER | Enrolled count | |
| **financial_year** | TEXT | FY | |
| **access_tier** | INTEGER | Visibility | DEFAULT 1 |
| **created_at** | TEXT | Timestamp | |

**Indexes**: `idx_strength_institute`, `idx_strength_program`, `idx_strength_year`

**Sample Queries**:
```sql
-- Admission gap analysis
SELECT 
    s.institute,
    s.program,
    s.intake AS sanctioned,
    COALESCE(a.total_students, 0) AS actual,
    s.intake - COALESCE(a.total_students, 0) AS gap,
    ROUND(COALESCE(a.total_students, 0) * 100.0 / NULLIF(s.intake, 0), 1) AS fill_pct
FROM sanctioned_intake s
LEFT JOIN actual_student_strength a
    ON s.institute = a.institute
    AND s.program = a.program
    AND s.financial_year = a.financial_year
WHERE s.financial_year = '2022-23'
ORDER BY gap DESC;
```

---

### phd_students
**Location**: `public.phd_students`
**Description**: PhD enrollment statistics.
**Primary Key**: `id` (TEXT)
**Update Frequency**: Annual

| Column | Type | Description | Notes |
|--------|------|-------------|-------|
| **id** | TEXT | Unique identifier | |
| **institute** | TEXT | Institution name | |
| **phd_students** | INTEGER | Number of PhD students | |
| **financial_year** | TEXT | FY | |
| **access_tier** | INTEGER | Visibility | DEFAULT 1 |
| **created_at** | TEXT | Timestamp | |

**Indexes**: `idx_phd_institute`, `idx_phd_year`

---

### financial_expenses_capital
**Location**: `public.financial_expenses_capital`
**Description**: Capital expenditure (infrastructure, equipment).
**Primary Key**: `id` (TEXT)
**Update Frequency**: Annual

| Column | Type | Description | Notes |
|--------|------|-------------|-------|
| **id** | TEXT | Unique identifier | |
| **institute** | TEXT | Institution name | |
| **financial_year** | TEXT | FY | |
| **[amount columns]** | REAL | Various capex categories | Check actual column names |
| **access_tier** | INTEGER | Visibility | DEFAULT 1 |
| **created_at** | TEXT | Timestamp | |

**Indexes**: `idx_capex_institute`, `idx_capex_year`

---

### financial_expenses_operational
**Location**: `public.financial_expenses_operational`
**Description**: Operational expenditure (salaries, maintenance).
**Primary Key**: `id` (TEXT)
**Update Frequency**: Annual

| Column | Type | Description | Notes |
|--------|------|-------------|-------|
| **id** | TEXT | Unique identifier | |
| **institute** | TEXT | Institution name | |
| **as_on_year** | TEXT | Year | |
| **[amount columns]** | REAL | Various opex categories | Check actual column names |
| **access_tier** | INTEGER | Visibility | DEFAULT 1 |
| **created_at** | TEXT | Timestamp | |

**Indexes**: `idx_opex_institute`, `idx_opex_year`

---

## Common Gotchas

1. **Financial year is TEXT everywhere**: '2020-21', '2021-22'. Use string comparison.

2. **Institute names must match exactly for joins**: `sanctioned_intake.institute` = `actual_student_strength.institute`. Spelling variations will break joins.

3. **NULL actual_student_strength means zero enrolled**: Use `COALESCE(total_students, 0)`.

4. **Capex/Opex column names vary**: Check actual schema before querying; may have category-specific columns.

5. **Program names may vary**: Same program could be 'B.Tech', 'B.Tech.', 'BTech'. Use `ILIKE` for fuzzy matching.
