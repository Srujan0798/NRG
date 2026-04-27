# NRG Key Metrics and KPIs

## Research Output Metrics

### Publication Count
- **Definition**: Total number of publications in the database
- **Formula**: `COUNT(*) FROM publications`
- **Source**: `publications.publication_id`
- **Time grain**: Usually by year (`year` column)
- **Caveats**: Publications without DOI may be preprints; no direct researcher linkage

### Citation-Weighted h-index (Approximate)
- **Definition**: Researcher impact metric
- **Formula**: Directly from `researchers.h_index` (pre-calculated)
- **Source**: `researchers.h_index`
- **Caveats**: Many NULL values; calculated externally, not live

### Researcher Count by State
- **Definition**: Number of active researchers per Indian state
- **Formula**: `COUNT(*) FROM researchers GROUP BY state`
- **Source**: `researchers.state`
- **Caveats**: `state` is free-text; standardization may be needed

---

## Funding Metrics

### Total Funding by Agency
- **Definition**: Sum of all grants from a specific funding agency
- **Formula**: `SUM(amount) FROM funding GROUP BY agency`
- **Source**: `funding.amount`, `funding.agency`
- **Caveats**: NULL amounts excluded; `agency` is free-text (may need normalization)

### Average Grant Size
- **Definition**: Mean funding amount per grant
- **Formula**: `AVG(amount) FROM funding WHERE amount IS NOT NULL`
- **Source**: `funding.amount`
- **Caveats**: Outliers (very large grants) can skew mean; use median for robustness

### Funding Duration
- **Definition**: Length of grant in days
- **Formula**: `end_date - start_date` (DATE subtraction)
- **Source**: `funding.start_date`, `funding.end_date`
- **Caveats**: NULL end_date means ongoing; use `CURRENT_DATE` as proxy

---

## Innovation & IP Metrics

### Patent Grant Rate
- **Definition**: Percentage of patent applications that were granted
- **Formula**: 
  ```sql
  COUNT(*) FILTER (WHERE status = 'Granted') * 100.0 / COUNT(*)
  FROM combined_ipo_patent_data
  ```
- **Source**: `combined_ipo_patent_data.status`
- **Caveats**: Pending applications ('Filed', 'Examined') may convert to 'Granted' later

### Patent Applications per Institute
- **Definition**: Count of patent filings by institution
- **Formula**: `COUNT(*) FROM combined_ipo_patent_data GROUP BY institute`
- **Source**: `combined_ipo_patent_data.institute`
- **Caveats**: `institute` is TEXT; same institution may have variant names

### TRL Distribution
- **Definition**: Distribution of innovations across Technology Readiness Levels
- **Formula**: `COUNT(*) GROUP BY stage_of_technology`
- **Source**: `innovations_at_various_stages_of_technology_readiness_level.stage_of_technology`
- **Caveats**: TRL scale 1-9; lower numbers = early research, higher = commercial

---

## Academic Operations Metrics

### Student Intake Gap
- **Definition**: Difference between sanctioned seats and actual enrollment
- **Formula**: 
  ```sql
  sanctioned_intake.intake - COALESCE(actual_student_strength.total_students, 0)
  ```
- **Source**: `sanctioned_intake.intake`, `actual_student_strength.total_students`
- **Caveats**: Join on (institute, program, financial_year); NULL actual means zero enrolled

### Fill Rate
- **Definition**: Percentage of sanctioned seats that are filled
- **Formula**: 
  ```sql
  COALESCE(actual_student_strength.total_students, 0) * 100.0 / NULLIF(sanctioned_intake.intake, 0)
  ```
- **Source**: Same as above
- **Caveats**: Can exceed 100% if supernumerary admissions exist

### PhD Completion Rate
- **Definition**: Ratio of PhD students to total student strength
- **Formula**: 
  ```sql
  phd_students.phd_students * 100.0 / actual_student_strength.total_students
  ```
- **Source**: `phd_students.phd_students`, `actual_student_strength.total_students`
- **Caveats**: Must join on (institute, financial_year); program-specific analysis possible

### Course Diversity
- **Definition**: Number of unique courses offered by an institution
- **Formula**: `COUNT(DISTINCT course_name) FROM academic_courses_details GROUP BY institute`
- **Source**: `academic_courses_details.course_name`
- **Caveats**: Same course may be listed under different names

---

## Financial Metrics

### Capital Expenditure (Capex)
- **Definition**: Infrastructure and equipment spending
- **Formula**: `SUM(amount) FROM financial_expenses_capital GROUP BY institute`
- **Source**: `financial_expenses_capital.amount` (or similar column)
- **Caveats**: Check exact column name in schema

### Operational Expenditure (Opex)
- **Definition**: Recurring operational spending
- **Formula**: `SUM(amount) FROM financial_expenses_operational GROUP BY institute`
- **Source**: `financial_expenses_operational.amount`
- **Caveats**: May include salaries, maintenance, utilities

### Capex-to-Opex Ratio
- **Definition**: Investment intensity
- **Formula**: `capex / opex`
- **Caveats**: Requires joining on (institute, financial_year); NULL handling critical

---

## Platform Quality Metrics

### Query Success Rate
- **Definition**: % of queries that return valid results
- **Formula**: 
  ```sql
  COUNT(*) FILTER (WHERE sql_row_count > 0) * 100.0 / COUNT(*)
  FROM training_pairs
  ```
- **Source**: `training_pairs.sql_row_count`
- **Caveats**: `route = 'text_to_sql'` only; excludes RAG-only queries

### Average Query Latency
- **Definition**: Time from query submission to response
- **Formula**: `AVG(latency_ms) FROM training_pairs`
- **Source**: `training_pairs.latency_ms`
- **Caveats**: Includes network time; breakdown in `node_timings` JSON

### GOLD Training Pair Rate
- **Definition**: % of queries graded as highest quality
- **Formula**: 
  ```sql
  COUNT(*) FILTER (WHERE quality_grade = 'GOLD') * 100.0 / COUNT(*)
  FROM training_pairs
  ```
- **Source**: `training_pairs.quality_grade`
- **Caveats**: Grading is post-hoc; may not reflect live user experience
