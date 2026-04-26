# Schema Value Synonyms

Text-to-SQL prompt guidance must normalize user wording to stored database values before SQL generation.

| User wording | Stored value or pattern |
| --- | --- |
| TRL 9, fully market ready, Market Ready | `stage_of_technology = 'Level 9'` |
| Lab Validation, lab validated, Level 4 | `stage_of_technology = 'Level 4'` |
| innovation credits, credit intensity | Parse `academic_courses_details.total_credit_score` as `X:Y` text |
| funding agency, grant provider | `innovation_grant_from_govt.gov_organisation_name` |
| granted patent, patent grants | `combined_ipo_patent_data.status = 'Granted'` |
| patent applicant, institute patent match | Normalize `combined_ipo_patent_data.applicants` against institute text |
