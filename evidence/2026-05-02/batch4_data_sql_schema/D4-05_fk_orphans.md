# D4-05 Foreign Key Orphan Report

| Child | Parent | Constraint present | Orphans | Status |
|---|---|---|---:|---|
| `researchers.institution_id` | `institutions.institution_id` | True | 0 | PASS |
| `funding_records.researcher_id` | `researchers.researcher_id` | True | 0 | PASS |
| `funding_records.institution_id` | `institutions.institution_id` | True | 0 | PASS |
| `funding_records.project_id` | `projects.project_id` | True | 0 | PASS |
| `projects.principal_investigator_id` | `researchers.researcher_id` | True | 0 | PASS |
| `researcher_publications.researcher_id` | `researchers.researcher_id` | True | 0 | PASS |
| `researcher_publications.publication_id` | `publications.publication_id` | True | 0 | PASS |
| `publication_keywords.publication_id` | `publications.publication_id` | True | 0 | PASS |
| `labs.institution_id` | `institutions.institution_id` | True | 0 | PASS |
