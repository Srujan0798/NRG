=== BASELINE SNAPSHOT ===
Date: 2026-04-25

1. DHAIRYA BENCHMARK:
   Result: 43/43 passed in 4.49s

2. AUDIT CHAIN:
   valid=False, errors=['Line 381369: hash mismatch'], count=381368

3. SCHEMA PARITY:
/Users/srujansai/Desktop/NRG/.venv/lib/python3.11/site-packages/pytest_asyncio/plugin.py:247: PytestDeprecationWarning: The configuration option "asyncio_default_fixture_loop_scope" is unset.
The event loop scope for asynchronous fixtures will default to the fixture caching scope. Future versions of pytest-asyncio will default the loop scope for asynchronous fixtures to function scope. Set the default fixture loop scope explicitly in order to avoid unexpected behavior in the future. Valid fixture loop scopes are: "function", "class", "module", "package", "session"

  warnings.warn(PytestDeprecationWarning(_DEFAULT_FIXTURE_LOOP_SCOPE_UNSET))
[1m============================= test session starts ==============================[0m
platform darwin -- Python 3.11.5, pytest-8.2.2, pluggy-1.6.0 -- /Users/srujansai/Desktop/NRG/.venv/bin/python
cachedir: .pytest_cache
rootdir: /Users/srujansai/Desktop/NRG
configfile: pytest.ini
plugins: cov-7.1.0, Faker-22.6.0, xdist-3.8.0, langsmith-0.7.32, asyncio-1.3.0, anyio-4.13.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
[1mcollecting ... [0mcollected 11 items

tests/data/test_schema_parity.py::TestSchemaParity::test_db_struct_sql_parseable [32mPASSED[0m[32m [  9%][0m
tests/data/test_schema_parity.py::TestSchemaParity::test_dhairya_tables_present [32mPASSED[0m[32m [ 18%][0m
tests/data/test_schema_parity.py::TestSchemaParity::test_live_db_connection [32mPASSED[0m[32m [ 27%][0m
tests/data/test_schema_parity.py::TestSchemaParity::test_live_db_has_all_tables [33mSKIPPED[0meed_funding', 'actual_student_strength',
'scraped_data_save', 'auth_group_permissions',
'combined_ipo_patent_data_old', 'scraped_data', 'fdp_details',
'financial_expenses_capital', 'advance_search_data_old',
'user_registration', 'startup_receiving_vc_investment',
'nirf_extracted_table', 'auth_group', 'scraped_raw_data',
'ipo_patent_details_flat_old', 'research_consultancy_details_sponsered',
'combined_ipo_patent_data', 'expertise', 'incubation_details',
'ipo_patent_details_flat', 'nirf_table_row',
'innovation_grant_from_govt', 'auth_user', 'academic_courses_details',
'auth_user_groups', 'django_admin_log', 'django_session', 'adv_se',
'faculty_details', 'faculty_strength',
'innovations_at_various_stages_of_technology_readiness_level',
'master_expertise', 'patents_details', 'financial_expenses_operational',
'auth_user_user_permissions', 'auth_permission', 'phd_students',
'nirf_pdf_record', 'startup_recognition_old', 'role_data',
'tb_institute_scrap_data_url', 'founders_of_fortune_500_companies',
'research_consultancy_details_consultancy', 'sanctioned_intake',
'tb_course_program_types', 'fdi_investment', 'package_data',
'startup_recognition', 'advance_search_data', 'django_content_type',
'tb_goi_ministries_mstr', 'django_migrations', 'tb_academic_year_mstr',
'tb_institute_mstr', 'startups_turnover_50_lacs',
'placements_and_higher_studies', 'user_registration_old',
'advance_search_data_15_12'}
assert not {'academic_courses_details',
'actual_student_strength', 'adv_se', 'advance_search_data',
'advance_search_data_15_12', 'advance_search_data_old', ...})[32m            [ 36%][0m
tests/data/test_schema_parity.py::TestSchemaParity::test_live_db_has_all_columns [32mPASSED[0m[32m [ 45%][0m
tests/data/test_schema_parity.py::TestSchemaParity::test_schema_fingerprint_stable [32mPASSED[0m[32m [ 54%][0m
tests/data/test_schema_parity.py::TestSchemaParity::test_schema_fingerprint_matches_expected [32mPASSED[0m[32m [ 63%][0m
tests/data/test_schema_parity.py::TestSchemaParity::test_all_dhairya_tables_have_minimum_rows [33mSKIPPED[0mcademic_courses_details"
does not exist
LINE 1: SELECT COUNT(*) FROM academic_courses_details
^

[SQL: SELECT COUNT(*) FROM academic_courses_details]
(Background on
this error at: https://sqlalche.me/e/20/f405))[32m                           [ 72%][0m
tests/data/test_schema_parity.py::TestSchemaParity::test_primary_keys_intact [33mSKIPPED[0mils', 'actual_student_strength', 'adv_se',
'advance_search_data', 'advance_search_data_15_12',
'advance_search_data_old', 'auth_group', 'auth_group_permissions',
'auth_permission', 'auth_user', 'auth_user_groups',
'auth_user_user_permissions', 'combined_ipo_patent_data',
'combined_ipo_patent_data_old', 'django_admin_log',
'django_content_type', 'django_migrations', 'django_session',
'expertise', 'faculty_details', 'faculty_strength', 'fdi_investment',
'fdp_details', 'financial_expenses_capital',
'financial_expenses_operational', 'founders_of_fortune_500_companies',
'incubation_details', 'innovation_grant_from_govt',
'innovations_at_various_stages_of_technology_readiness_level',
'ipo_patent_details_flat', 'ipo_patent_details_flat_old',
'master_expertise', 'nirf_extracted_table', 'nirf_pdf_record',
'nirf_table_row', 'package_data', 'patents_details', 'phd_students',
'placements_and_higher_studies',
'research_consultancy_details_consultancy',
'research_consultancy_details_sponsered', 'role_data',
'sanctioned_intake', 'scraped_data', 'scraped_data_save',
'scraped_raw_data', 'seed_funding', 'startup_receiving_vc_investment',
'startup_recognition_old', 'startup_recognition',
'startups_turnover_50_lacs', 'tb_academic_year_mstr',
'tb_course_program_types', 'tb_goi_ministries_mstr',
'tb_institute_mstr', 'tb_institute_scrap_data_url', 'user_registration',
'user_registration_old']
assert not ['academic_courses_details',
'actual_student_strength', 'adv_se', 'advance_search_data',
'advance_search_data_15_12', 'advance_search_data_old', ...])[32m            [ 81%][0m
tests/data/test_schema_parity.py::TestSchemaParity::test_no_orphan_foreign_keys [32mPASSED[0m[32m [ 90%][0m
tests/data/test_schema_parity.py::TestSchemaParity::test_total_credit_score_is_text_type [33mSKIPPED[0m[32m [100%][0m/Users/srujansai/Desktop/NRG/.venv/lib/python3.11/site-packages/coverage/control.py:958: CoverageWarning: No data was collected. (no-data-collected); see https://coverage.readthedocs.io/en/7.13.5/messages.html#warning-no-data-collected
  self._warn("No data was collected.", slug="no-data-collected")


================================ tests coverage ================================
_______________ coverage: platform darwin, python 3.11.5-final-0 _______________

Name                                                Stmts   Miss  Cover   Missing
---------------------------------------------------------------------------------
src/__init__.py                                         0      0   100%
src/api/__init__.py                                     0      0   100%
src/api/logging_config.py                              57     57     0%   6-121
src/api/main.py                                      1265   1265     0%   6-2489
src/audit/__init__.py                                 341    341     0%   8-665
src/audit/db_cosign.py                                163    163     0%   17-402
src/audit/per_user_keys.py                            112    112     0%   17-212
src/auth/__init__.py                                    2      2     0%   3-5
src/auth/jwt_handler.py                               152    152     0%   3-345
src/auth/middleware.py                                101    101     0%   3-253
src/auth/rbac.py                                      294    294     0%   17-574
src/auth/refresh_store.py                              65     65     0%   3-151
src/caching/__init__.py                                 0      0   100%
src/caching/redis_layer.py                             64     64     0%   1-108
src/config/__init__.py                                  2      2     0%   3-14
src/config/database.py                                189    189     0%   9-295
src/config/llm_config.py                              854    854     0%   3-1575
src/config/local_llm.py                               232    232     0%   7-421
src/data/__init__.py                                    0      0   100%
src/data/database.py                                   80     80     0%   3-171
src/data/database_v2.py                               397    397     0%   7-873
src/data/metadata/__init__.py                           0      0   100%
src/data/metadata/access_control_labels.py             66     66     0%   6-219
src/db/__init__.py                                      0      0   100%
src/db/seed.py                                         24     24     0%   3-43
src/orchestration/__init__.py                           0      0   100%
src/orchestration/checkpoint.py                       102    102     0%   3-187
src/orchestration/graph.py                            160    160     0%   3-256
src/orchestration/nodes/__init__.py                     0      0   100%
src/orchestration/nodes/complexity_classifier.py       71     71     0%   15-180
src/orchestration/nodes/executor.py                   216    216     0%   3-375
src/orchestration/nodes/planner.py                    282    282     0%   3-578
src/orchestration/nodes/receiver.py                    40     40     0%   3-74
src/orchestration/nodes/reflector.py                   27     27     0%   7-78
src/orchestration/nodes/retry_handler.py               31     31     0%   7-80
src/orchestration/nodes/router.py                     398    398     0%   20-921
src/orchestration/nodes/synthesizer.py                655    655     0%   3-1297
src/orchestration/nodes/verifier.py                   279    279     0%   3-570
src/orchestration/state.py                             85     85     0%   3-125
src/orchestration/workflows/__init__.py                 0      0   100%
src/orchestration/workflows/multi_hop.py               21     21     0%   22-76
src/security/__init__.py                                0      0   100%
src/security/dpdp_compliance.py                        70     70     0%   8-181
src/security/egress_guard/__init__.py                 139    139     0%   14-242
src/security/gateway/__init__.py                        0      0   100%
src/security/gateway/prompt_sanitiser.py              145    145     0%   1-515
src/security/headers.py                                38     38     0%   11-85
src/security/pii/__init__.py                           49     49     0%   3-110
src/security/pii/fpe_engine.py                         60     60     0%   1-130
src/security/pii/presidio_config.py                   103    103     0%   3-224
src/security/pii/tokenizer.py                          72     72     0%   1-177
src/security/pii/verhoeff.py                           16     16     0%   8-69
src/security/pii_encryption.py                        102    102     0%   8-170
src/security/query_allowlist.py                        59     59     0%   9-171
src/security/rate_limiter.py                          124    124     0%   14-285
src/security/rbac/__init__.py                           0      0   100%
src/security/rbac/middleware.py                        30     30     0%   7-120
src/security/rbac/postgresql_rbac.py                  102    102     0%   7-326
src/security/rbac/qdrant_rbac.py                      102    102     0%   7-251
src/security/request_signer.py                         57     57     0%   8-150
src/security/security_harden.py                         8      8     0%   16-24
src/security/token_rotation.py                         60     60     0%   9-191
src/skills/__init__.py                                  0      0   100%
src/skills/rag/__init__.py                              2      2     0%   3-5
src/skills/rag/embedder.py                            191    191     0%   3-285
src/skills/rag/ingest.py                               68     68     0%   3-121
src/skills/rag/reranker.py                             38     38     0%   3-57
src/skills/rag/retriever.py                           245    245     0%   3-547
src/skills/rag/skill.py                                80     80     0%   3-151
src/skills/text_to_sql/__init__.py                      0      0   100%
src/skills/text_to_sql/sandbox.py                      74     74     0%   3-170
src/skills/text_to_sql/schema_extractor.py            144    144     0%   7-411
src/skills/text_to_sql/schema_sync_check.py           199    199     0%   7-390
src/skills/text_to_sql/skill.py                       555    555     0%   3-1138
src/skills/text_to_sql/sql_examples.py                 29     29     0%   13-340
src/skills/text_to_sql/sql_oracle.py                  152    152     0%   17-322
src/skills/text_to_sql/sqlite_sandbox.py               57     57     0%   3-128
src/skills/text_to_sql/sqlite_schema_extractor.py     120    120     0%   3-418
src/skills/text_to_sql/table_relationships.py          35     35     0%   7-633
src/skills/text_to_sql/validator.py                   136    136     0%   3-329
src/training/__init__.py                                5      5     0%   3-12
src/training/data_collector.py                        164    164     0%   7-375
src/training/data_formatter.py                        119    119     0%   9-248
src/training/export.py                                 78     78     0%   6-171
src/training/quality_filter.py                        103    103     0%   7-180
src/training/stratified_sampler.py                    152    152     0%   14-254
src/utils/__init__.py                                   0      0   100%
src/utils/helpers.py                                   32     32     0%   6-63
src/utils/logging_config.py                            40     40     0%   6-87
---------------------------------------------------------------------------------
TOTAL                                               10981  10981     0%
Coverage XML written to file coverage.xml
[32m========================= [32m[1m7 passed[0m, [33m4 skipped[0m[32m in 3.94s[0m[32m =========================[0m

4. EGRESS ALLOWLIST:
/Users/srujansai/Desktop/NRG/.venv/lib/python3.11/site-packages/pytest_asyncio/plugin.py:247: PytestDeprecationWarning: The configuration option "asyncio_default_fixture_loop_scope" is unset.
The event loop scope for asynchronous fixtures will default to the fixture caching scope. Future versions of pytest-asyncio will default the loop scope for asynchronous fixtures to function scope. Set the default fixture loop scope explicitly in order to avoid unexpected behavior in the future. Valid fixture loop scopes are: "function", "class", "module", "package", "session"

  warnings.warn(PytestDeprecationWarning(_DEFAULT_FIXTURE_LOOP_SCOPE_UNSET))
[1m============================= test session starts ==============================[0m
platform darwin -- Python 3.11.5, pytest-8.2.2, pluggy-1.6.0 -- /Users/srujansai/Desktop/NRG/.venv/bin/python
cachedir: .pytest_cache
rootdir: /Users/srujansai/Desktop/NRG
configfile: pytest.ini
plugins: cov-7.1.0, Faker-22.6.0, xdist-3.8.0, langsmith-0.7.32, asyncio-1.3.0, anyio-4.13.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
[1mcollecting ... [0mcollected 35 items

tests/security/test_egress_allowlist.py::TestEgressSchemaAllowlistLoader::test_is_table_allowed_valid [32mPASSED[0m[32m [  2%][0m
tests/security/test_egress_allowlist.py::TestEgressSchemaAllowlistLoader::test_is_table_allowed_invalid [32mPASSED[0m[32m [  5%][0m
tests/security/test_egress_allowlist.py::TestEgressSchemaAllowlistLoader::test_is_column_allowed_valid [32mPASSED[0m[32m [  8%][0m
tests/security/test_egress_allowlist.py::TestEgressSchemaAllowlistLoader::test_is_column_allowed_blocked [32mPASSED[0m[32m [ 11%][0m
tests/security/test_egress_allowlist.py::TestEgressSchemaAllowlistLoader::test_get_blocked_content_returns_frozenset [32mPASSED[0m[32m [ 14%][0m
tests/security/test_egress_allowlist.py::TestEgressSchemaAllowlistLoader::test_is_llm_prompt_allowed [32mPASSED[0m[32m [ 17%][0m
tests/security/test_egress_allowlist.py::TestEgressSchemaAllowlistLoader::test_get_allowed_tables [32mPASSED[0m[32m [ 20%][0m
tests/security/test_egress_allowlist.py::TestEgressSchemaAllowlistLoader::test_get_table_columns [32mPASSED[0m[32m [ 22%][0m
tests/security/test_egress_allowlist.py::TestSovereignHTTPXClientAllowed::test_allowed_user_query [32mPASSED[0m[32m [ 25%][0m
tests/security/test_egress_allowlist.py::TestSovereignHTTPXClientAllowed::test_allowed_schema_prompt_valid_table [32mPASSED[0m[32m [ 28%][0m
tests/security/test_egress_allowlist.py::TestSovereignHTTPXClientAllowed::test_allowed_plan_json [32mPASSED[0m[32m [ 31%][0m
tests/security/test_egress_allowlist.py::TestSovereignHTTPXClientAllowed::test_allowed_citation_ids [32mPASSED[0m[32m [ 34%][0m
tests/security/test_egress_allowlist.py::TestSovereignHTTPXClientAllowed::test_allowed_session_id [32mPASSED[0m[32m [ 37%][0m
tests/security/test_egress_allowlist.py::TestSovereignHTTPXClientBlockedTables::test_blocked_unlisted_table_in_schema_prompt [32mPASSED[0m[32m [ 40%][0m
tests/security/test_egress_allowlist.py::TestSovereignHTTPXClientBlockedTables::test_blocked_unlisted_table_join [32mPASSED[0m[32m [ 42%][0m
tests/security/test_egress_allowlist.py::TestSovereignHTTPXClientBlockedTables::test_blocked_user_credentials_table [32mPASSED[0m[32m [ 45%][0m
tests/security/test_egress_allowlist.py::TestSovereignHTTPXClientBlockedTables::test_blocked_passwords_table [32mPASSED[0m[32m [ 48%][0m
tests/security/test_egress_allowlist.py::TestSovereignHTTPXClientBlockedTables::test_blocked_private_notes_table [32mPASSED[0m[32m [ 51%][0m
tests/security/test_egress_allowlist.py::TestSovereignHTTPXClientBlockedColumns::test_blocked_email_column [32mPASSED[0m[32m [ 54%][0m
tests/security/test_egress_allowlist.py::TestSovereignHTTPXClientBlockedColumns::test_blocked_phone_column [32mPASSED[0m[32m [ 57%][0m
tests/security/test_egress_allowlist.py::TestSovereignHTTPXClientBlockedColumns::test_blocked_full_text_field [32mPASSED[0m[32m [ 60%][0m
tests/security/test_egress_allowlist.py::TestSovereignHTTPXClientBlockedColumns::test_blocked_fulltext_nested [32mPASSED[0m[32m [ 62%][0m
tests/security/test_egress_allowlist.py::TestSovereignHTTPXClientBlockedColumns::test_blocked_researcher_table_column_in_schema [32mPASSED[0m[32m [ 65%][0m
tests/security/test_egress_allowlist.py::TestSovereignHTTPXClientBlockedPatterns::test_blocked_raw_content_field [32mPASSED[0m[32m [ 68%][0m
tests/security/test_egress_allowlist.py::TestSovereignHTTPXClientBlockedPatterns::test_blocked_raw_db_dump [32mPASSED[0m[32m [ 71%][0m
tests/security/test_egress_allowlist.py::TestSovereignHTTPXClientBlockedPatterns::test_blocked_publication_text [32mPASSED[0m[32m [ 74%][0m
tests/security/test_egress_allowlist.py::TestSovereignHTTPXClientBlockedPatterns::test_blocked_research_content [32mPASSED[0m[32m [ 77%][0m
tests/security/test_egress_allowlist.py::TestSovereignHTTPXClientBlockedPatterns::test_blocked_full_publication_record [32mPASSED[0m[32m [ 80%][0m
tests/security/test_egress_allowlist.py::TestYAMLHotReload::test_reload_on_mtime_change [32mPASSED[0m[32m [ 82%][0m
tests/security/test_egress_allowlist.py::TestYAMLHotReload::test_singleton_same_instance [32mPASSED[0m[32m [ 85%][0m
tests/security/test_egress_allowlist.py::TestFalsePositives::test_researcher_name_not_blocked [32mPASSED[0m[32m [ 88%][0m
tests/security/test_egress_allowlist.py::TestFalsePositives::test_publication_title_not_blocked [32mPASSED[0m[32m [ 91%][0m
tests/security/test_egress_allowlist.py::TestFalsePositives::test_institution_name_not_blocked [32mPASSED[0m[32m [ 94%][0m
tests/security/test_egress_allowlist.py::TestFalsePositives::test_complex_query_with_multiple_tables [32mPASSED[0m[32m [ 97%][0m
tests/security/test_egress_allowlist.py::TestFalsePositives::test_aggregate_query [32mPASSED[0m[32m [100%][0m

================================ tests coverage ================================
_______________ coverage: platform darwin, python 3.11.5-final-0 _______________

Name                                                Stmts   Miss  Cover   Missing
---------------------------------------------------------------------------------
src/__init__.py                                         0      0   100%
src/api/__init__.py                                     0      0   100%
src/api/logging_config.py                              57     57     0%   6-121
src/api/main.py                                      1265   1265     0%   6-2489
src/audit/__init__.py                                 341    168    51%   24, 90-91, 108-111, 123, 175, 182, 185, 196-197, 206, 217-227, 251-287, 291-349, 370, 384-385, 395-401, 405-421, 424, 427, 437, 442, 454, 470, 487-528, 535, 549-556, 563-587, 591, 595-600, 614, 618, 622, 626, 630, 635, 644-651, 665
src/audit/db_cosign.py                                163    107    34%   51, 57, 62, 72-75, 92, 162-167, 185-228, 241-278, 286-328, 339-361, 389-393, 402
src/audit/per_user_keys.py                            112     57    49%   49, 57-58, 61-66, 69-82, 85-86, 109-132, 143-145, 157-172, 182-187, 210-212
src/auth/__init__.py                                    2      2     0%   3-5
src/auth/jwt_handler.py                               152    152     0%   3-345
src/auth/middleware.py                                101    101     0%   3-253
src/auth/rbac.py                                      294    294     0%   17-574
src/auth/refresh_store.py                              65     65     0%   3-151
src/caching/__init__.py                                 0      0   100%
src/caching/redis_layer.py                             64     64     0%   1-108
src/config/__init__.py                                  2      2     0%   3-14
src/config/database.py                                189    189     0%   9-295
src/config/llm_config.py                              854    854     0%   3-1575
src/config/local_llm.py                               232    232     0%   7-421
src/data/__init__.py                                    0      0   100%
src/data/database.py                                   80     80     0%   3-171
src/data/database_v2.py                               397    397     0%   7-873
src/data/metadata/__init__.py                           0      0   100%
src/data/metadata/access_control_labels.py             66     66     0%   6-219
src/db/__init__.py                                      0      0   100%
src/db/seed.py                                         24     24     0%   3-43
src/orchestration/__init__.py                           0      0   100%
src/orchestration/checkpoint.py                       102    102     0%   3-187
src/orchestration/graph.py                            160    160     0%   3-256
src/orchestration/nodes/__init__.py                     0      0   100%
src/orchestration/nodes/complexity_classifier.py       71     71     0%   15-180
src/orchestration/nodes/executor.py                   216    216     0%   3-375
src/orchestration/nodes/planner.py                    282    282     0%   3-578
src/orchestration/nodes/receiver.py                    40     40     0%   3-74
src/orchestration/nodes/reflector.py                   27     27     0%   7-78
src/orchestration/nodes/retry_handler.py               31     31     0%   7-80
src/orchestration/nodes/router.py                     398    398     0%   20-921
src/orchestration/nodes/synthesizer.py                655    655     0%   3-1297
src/orchestration/nodes/verifier.py                   279    279     0%   3-570
src/orchestration/state.py                             85     85     0%   3-125
src/orchestration/workflows/__init__.py                 0      0   100%
src/orchestration/workflows/multi_hop.py               21     21     0%   22-76
src/security/__init__.py                                0      0   100%
src/security/dpdp_compliance.py                        70     70     0%   8-181
src/security/egress/guard.py                          180     57    68%   29, 45-48, 85-91, 99, 128, 137, 146-147, 154-160, 208-214, 217, 227-232, 266-267, 280-289, 293, 297, 300, 303, 308-320, 325
src/security/egress/schema_allowlist_loader.py         57      8    86%   31-32, 83-88
src/security/egress_guard/__init__.py                 139    139     0%   14-242
src/security/gateway/__init__.py                        0      0   100%
src/security/gateway/prompt_sanitiser.py              145    145     0%   1-515
src/security/headers.py                                38     38     0%   11-85
src/security/pii/__init__.py                           49     49     0%   3-110
src/security/pii/fpe_engine.py                         60     60     0%   1-130
src/security/pii/presidio_config.py                   103    103     0%   3-224
src/security/pii/tokenizer.py                          72     72     0%   1-177
src/security/pii/verhoeff.py                           16     16     0%   8-69
src/security/pii_encryption.py                        102    102     0%   8-170
src/security/query_allowlist.py                        59     59     0%   9-171
src/security/rate_limiter.py                          124    124     0%   14-285
src/security/rbac/__init__.py                           0      0   100%
src/security/rbac/middleware.py                        30     30     0%   7-120
src/security/rbac/postgresql_rbac.py                  102    102     0%   7-326
src/security/rbac/qdrant_rbac.py                      102    102     0%   7-251
src/security/request_signer.py                         57     57     0%   8-150
src/security/security_harden.py                         8      8     0%   16-24
src/security/token_rotation.py                         60     60     0%   9-191
src/skills/__init__.py                                  0      0   100%
src/skills/rag/__init__.py                              2      2     0%   3-5
src/skills/rag/embedder.py                            191    191     0%   3-285
src/skills/rag/ingest.py                               68     68     0%   3-121
src/skills/rag/reranker.py                             38     38     0%   3-57
src/skills/rag/retriever.py                           245    245     0%   3-547
src/skills/rag/skill.py                                80     80     0%   3-151
src/skills/text_to_sql/__init__.py                      0      0   100%
src/skills/text_to_sql/sandbox.py                      74     74     0%   3-170
src/skills/text_to_sql/schema_extractor.py            144    144     0%   7-411
src/skills/text_to_sql/schema_sync_check.py           199    199     0%   7-390
src/skills/text_to_sql/skill.py                       555    555     0%   3-1138
src/skills/text_to_sql/sql_examples.py                 29     29     0%   13-340
src/skills/text_to_sql/sql_oracle.py                  152    152     0%   17-322
src/skills/text_to_sql/sqlite_sandbox.py               57     57     0%   3-128
src/skills/text_to_sql/sqlite_schema_extractor.py     120    120     0%   3-418
src/skills/text_to_sql/table_relationships.py          35     35     0%   7-633
src/skills/text_to_sql/validator.py                   136    136     0%   3-329
src/training/__init__.py                                5      5     0%   3-12
src/training/data_collector.py                        164    164     0%   7-375
src/training/data_formatter.py                        119    119     0%   9-248
src/training/export.py                                 78     78     0%   6-171
src/training/quality_filter.py                        103    103     0%   7-180
src/training/stratified_sampler.py                    152    152     0%   14-254
src/utils/__init__.py                                   0      0   100%
src/utils/helpers.py                                   32     32     0%   6-63
src/utils/logging_config.py                            40     40     0%   6-87
---------------------------------------------------------------------------------
TOTAL                                               11218  10762     4%
Coverage XML written to file coverage.xml
[32m============================== [32m[1m35 passed[0m[32m in 3.48s[0m[32m ==============================[0m

5. MULTI-HOP PLANNER:
/Users/srujansai/Desktop/NRG/.venv/lib/python3.11/site-packages/pytest_asyncio/plugin.py:247: PytestDeprecationWarning: The configuration option "asyncio_default_fixture_loop_scope" is unset.
The event loop scope for asynchronous fixtures will default to the fixture caching scope. Future versions of pytest-asyncio will default the loop scope for asynchronous fixtures to function scope. Set the default fixture loop scope explicitly in order to avoid unexpected behavior in the future. Valid fixture loop scopes are: "function", "class", "module", "package", "session"

  warnings.warn(PytestDeprecationWarning(_DEFAULT_FIXTURE_LOOP_SCOPE_UNSET))
[1m============================= test session starts ==============================[0m
platform darwin -- Python 3.11.5, pytest-8.2.2, pluggy-1.6.0 -- /Users/srujansai/Desktop/NRG/.venv/bin/python
cachedir: .pytest_cache
rootdir: /Users/srujansai/Desktop/NRG
configfile: pytest.ini
plugins: cov-7.1.0, Faker-22.6.0, xdist-3.8.0, langsmith-0.7.32, asyncio-1.3.0, anyio-4.13.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
[1mcollecting ... [0mcollected 28 items / 28 deselected / 0 selected

================================ tests coverage ================================
_______________ coverage: platform darwin, python 3.11.5-final-0 _______________

Name                                                Stmts   Miss  Cover   Missing
---------------------------------------------------------------------------------
src/__init__.py                                         0      0   100%
src/api/__init__.py                                     0      0   100%
src/api/logging_config.py                              57     57     0%   6-121
src/api/main.py                                      1265   1265     0%   6-2489
src/audit/__init__.py                                 341    273    20%   24, 54-69, 72-81, 84, 88-91, 108-111, 114-118, 121-141, 148-159, 166-167, 174-177, 180-182, 185, 188-189, 196-197, 205-247, 251-287, 291-349, 353-356, 360-376, 384-385, 395-401, 405-421, 424, 427, 437, 442, 454, 470, 487-528, 535, 549-556, 563-587, 591, 595-600, 608-610, 614, 618, 622, 626, 630, 635, 644-651, 665
src/audit/db_cosign.py                                163    163     0%   17-402
src/audit/per_user_keys.py                            112    112     0%   17-212
src/auth/__init__.py                                    2      2     0%   3-5
src/auth/jwt_handler.py                               152    152     0%   3-345
src/auth/middleware.py                                101    101     0%   3-253
src/auth/rbac.py                                      294    294     0%   17-574
src/auth/refresh_store.py                              65     65     0%   3-151
src/caching/__init__.py                                 0      0   100%
src/caching/redis_layer.py                             64     64     0%   1-108
src/config/__init__.py                                  2      0   100%
src/config/database.py                                189    141    25%   58-67, 71-75, 78-80, 83-92, 95-114, 118-125, 129-141, 146-151, 155-164, 168-177, 181-182, 187-201, 205-218, 226-246, 250-260, 264-266, 276-284, 293-295
src/config/llm_config.py                              854    743    13%   63, 67-70, 74-155, 162, 170-202, 211-254, 259, 267-309, 318-367, 372, 380-417, 426-470, 475, 483-522, 527-535, 543-572, 577-597, 604-605, 613-645, 654-697, 713-738, 742-748, 752-772, 776-795, 799-802, 813-838, 845-859, 863-865, 869-880, 887-900, 904-927, 931-946, 950-954, 965-980, 999-1053, 1060-1064, 1079-1126, 1130, 1134-1167, 1171-1195, 1204-1206, 1270-1279, 1282-1288, 1291-1292, 1295-1304, 1307-1315, 1319-1323, 1327-1328, 1331-1335, 1344-1357, 1360, 1365-1366, 1382-1385, 1397-1403, 1420-1451, 1455-1467, 1481-1494, 1497-1502, 1505-1558, 1562-1575
src/config/local_llm.py                               232    232     0%   7-421
src/data/__init__.py                                    0      0   100%
src/data/database.py                                   80     80     0%   3-171
src/data/database_v2.py                               397    397     0%   7-873
src/data/metadata/__init__.py                           0      0   100%
src/data/metadata/access_control_labels.py             66     66     0%   6-219
src/db/__init__.py                                      0      0   100%
src/db/seed.py                                         24     24     0%   3-43
src/observability/langfuse_tracer.py                  246    205    17%   29-47, 51, 60-97, 111-168, 173-206, 211-243, 248-281, 292-307, 312-326, 340-347, 350-361, 364-368, 372-376, 380-393, 397-409, 413-415, 427
src/orchestration/__init__.py                           0      0   100%
src/orchestration/checkpoint.py                       102    102     0%   3-187
src/orchestration/graph.py                            160    160     0%   3-256
src/orchestration/nodes/__init__.py                     0      0   100%
src/orchestration/nodes/complexity_classifier.py       71     71     0%   15-180
src/orchestration/nodes/executor.py                   216    170    21%   36-37, 58-65, 71-78, 83-111, 116-157, 163-187, 199-235, 240-256, 261-263, 281-301, 306-375
src/orchestration/nodes/planner.py                    282    231    18%   79-88, 104-174, 186-191, 200-308, 321-329, 334-336, 341-359, 364-374, 379-396, 400-406, 410, 423-450, 459-460, 471-483, 493-494, 499-507, 512, 516-528, 532-541, 545-547, 556-578
src/orchestration/nodes/receiver.py                    40     40     0%   3-74
src/orchestration/nodes/reflector.py                   27     27     0%   7-78
src/orchestration/nodes/retry_handler.py               31     31     0%   7-80
src/orchestration/nodes/router.py                     398    398     0%   20-921
src/orchestration/nodes/synthesizer.py                655    655     0%   3-1297
src/orchestration/nodes/verifier.py                   279    279     0%   3-570
src/orchestration/state.py                             85     14    84%   22, 32, 88-96, 99, 104, 107, 111, 115, 118-120, 124-125
src/orchestration/workflows/__init__.py                 0      0   100%
src/orchestration/workflows/multi_hop.py               21     21     0%   22-76
src/security/__init__.py                                0      0   100%
src/security/dpdp_compliance.py                        70     70     0%   8-181
src/security/egress/guard.py                          180    149    17%   29, 34-48, 61-63, 78-81, 85-91, 98-160, 167-239, 246-250, 254-271, 280-289, 293, 297, 300, 303, 308-320, 325
src/security/egress/schema_allowlist_loader.py         57     38    33%   23-25, 29-39, 43-44, 48-52, 56-58, 62-64, 68-69, 73-76, 83-88, 93
src/security/egress_guard/__init__.py                 139    139     0%   14-242
src/security/gateway/__init__.py                        0      0   100%
src/security/gateway/prompt_sanitiser.py              145    145     0%   1-515
src/security/headers.py                                38     38     0%   11-85
src/security/pii/__init__.py                           49     49     0%   3-110
src/security/pii/fpe_engine.py                         60     60     0%   1-130
src/security/pii/presidio_config.py                   103    103     0%   3-224
src/security/pii/tokenizer.py                          72     72     0%   1-177
src/security/pii/verhoeff.py                           16     16     0%   8-69
src/security/pii_encryption.py                        102    102     0%   8-170
src/security/query_allowlist.py                        59     37    37%   63-72, 82, 87-91, 96-99, 106, 110-124, 133-140, 144, 152-154, 166, 171
src/security/rate_limiter.py                          124    124     0%   14-285
src/security/rbac/__init__.py                           0      0   100%
src/security/rbac/middleware.py                        30     30     0%   7-120
src/security/rbac/postgresql_rbac.py                  102    102     0%   7-326
src/security/rbac/qdrant_rbac.py                      102    102     0%   7-251
src/security/request_signer.py                         57     57     0%   8-150
src/security/security_harden.py                         8      8     0%   16-24
src/security/token_rotation.py                         60     60     0%   9-191
src/skills/__init__.py                                  0      0   100%
src/skills/rag/__init__.py                              2      0   100%
src/skills/rag/embedder.py                            191    155    19%   30-31, 35-61, 65-67, 71, 75-82, 96, 99-117, 120, 127-131, 135-173, 177-210, 214-217, 221-235, 239, 243, 247-249, 253-257, 260, 265-282, 285
src/skills/rag/ingest.py                               68     68     0%   3-121
src/skills/rag/reranker.py                             38     38     0%   3-57
src/skills/rag/retriever.py                           245    210    14%   40-50, 62-94, 103-124, 128-132, 136-148, 152-154, 173-189, 193, 202-218, 225-231, 247-341, 355-367, 375-382, 385-403, 409-410, 414-419, 423-431, 435-493, 497-533, 536, 541-543, 547
src/skills/rag/skill.py                                80     63    21%   20-21, 25-36, 47-82, 86-109, 113-115, 125-126, 131-147, 151
src/skills/text_to_sql/__init__.py                      0      0   100%
src/skills/text_to_sql/sandbox.py                      74     74     0%   3-170
src/skills/text_to_sql/schema_extractor.py            144    144     0%   7-411
src/skills/text_to_sql/schema_sync_check.py           199    199     0%   7-390
src/skills/text_to_sql/skill.py                       555    503     9%   49-74, 77-83, 86-89, 92-96, 101-129, 132-135, 138-147, 150, 215-218, 222-231, 235-244, 254-259, 263-275, 281-296, 300-388, 444-501, 505-522, 526-672, 676-808, 812-861, 868-913, 917-937, 941-951, 955-986, 990-1014, 1025-1101, 1105-1111, 1115-1116, 1121-1134, 1138
src/skills/text_to_sql/sql_examples.py                 29     24    17%   306-325, 330-340
src/skills/text_to_sql/sql_oracle.py                  152    152     0%   17-322
src/skills/text_to_sql/sqlite_sandbox.py               57     57     0%   3-128
src/skills/text_to_sql/sqlite_schema_extractor.py     120     98    18%   141-144, 148-151, 155, 162-170, 174-184, 188-196, 200-211, 221-252, 260-293, 302-374, 381-389, 393, 397-401, 405-409, 414-418
src/skills/text_to_sql/table_relationships.py          35     35     0%   7-633
src/skills/text_to_sql/validator.py                   136    107    21%   22-23, 31-57, 61-62, 66-68, 72-74, 78-87, 91-98, 102-110, 139-141, 149-179, 183-189, 193-211, 215-217, 313-323, 327-329
src/training/__init__.py                                5      5     0%   3-12
src/training/data_collector.py                        164    164     0%   7-375
src/training/data_formatter.py                        119    119     0%   9-248
src/training/export.py                                 78     78     0%   6-171
src/training/quality_filter.py                        103    103     0%   7-180
src/training/stratified_sampler.py                    152    152     0%   14-254
src/utils/__init__.py                                   0      0   100%
src/utils/helpers.py                                   32     32     0%   6-63
src/utils/logging_config.py                            40     40     0%   6-87
---------------------------------------------------------------------------------
TOTAL                                               11464  10756     6%
Coverage XML written to file coverage.xml
[33m============================ [33m[1m28 deselected[0m[33m in 3.25s[0m[33m ============================[0m
6. VECTOR DRIFT:
/Users/srujansai/Desktop/NRG/.venv/lib/python3.11/site-packages/pytest_asyncio/plugin.py:247: PytestDeprecationWarning: The configuration option "asyncio_default_fixture_loop_scope" is unset.
The event loop scope for asynchronous fixtures will default to the fixture caching scope. Future versions of pytest-asyncio will default the loop scope for asynchronous fixtures to function scope. Set the default fixture loop scope explicitly in order to avoid unexpected behavior in the future. Valid fixture loop scopes are: "function", "class", "module", "package", "session"

  warnings.warn(PytestDeprecationWarning(_DEFAULT_FIXTURE_LOOP_SCOPE_UNSET))
[1m============================= test session starts ==============================[0m
platform darwin -- Python 3.11.5, pytest-8.2.2, pluggy-1.6.0 -- /Users/srujansai/Desktop/NRG/.venv/bin/python
cachedir: .pytest_cache
rootdir: /Users/srujansai/Desktop/NRG
configfile: pytest.ini
plugins: cov-7.1.0, Faker-22.6.0, xdist-3.8.0, langsmith-0.7.32, asyncio-1.3.0, anyio-4.13.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
[1mcollecting ... [0mcollected 17 items

tests/observability/test_vector_drift.py::TestCosineShift::test_identical_vectors_near_zero_shift [32mPASSED[0m[32m [  5%][0m
tests/observability/test_vector_drift.py::TestCosineShift::test_opposite_vectors_max_shift [32mPASSED[0m[32m [ 11%][0m
tests/observability/test_vector_drift.py::TestCosineShift::test_orthogonal_vectors_high_shift [32mPASSED[0m[32m [ 17%][0m
tests/observability/test_vector_drift.py::TestTriggerReindex::test_trigger_posts_to_reindex_endpoint [32mPASSED[0m[32m [ 23%][0m
tests/observability/test_vector_drift.py::TestTriggerReindex::test_trigger_skips_when_no_token [32mPASSED[0m[32m [ 29%][0m
tests/observability/test_vector_drift.py::TestCheckCosineShift::test_no_reference_establishes_baseline [32mPASSED[0m[32m [ 35%][0m
tests/observability/test_vector_drift.py::TestCheckCosineShift::test_shift_above_threshold_triggers_reindex [32mPASSED[0m[32m [ 41%][0m
tests/observability/test_vector_drift.py::TestCheckCosineShift::test_stable_when_shift_below_threshold [32mPASSED[0m[32m [ 47%][0m
tests/observability/test_vector_drift.py::TestSLOThresholds::test_drift_slo_exactly_085 [32mPASSED[0m[32m [ 52%][0m
tests/observability/test_vector_drift.py::TestSLOThresholds::test_cosine_shift_threshold_exactly_005 [32mPASSED[0m[32m [ 58%][0m
tests/observability/test_vector_drift.py::TestSLOThresholds::test_benchmark_queries_count [32mPASSED[0m[32m [ 64%][0m
tests/observability/test_vector_drift.py::TestDriftCheckRuntime::test_qdrant_unhealthy_is_not_benchmark_ready [32mPASSED[0m[32m [ 70%][0m
tests/observability/test_vector_drift.py::TestDriftCheckRuntime::test_qdrant_empty_collection_is_not_benchmark_ready [32mPASSED[0m[32m [ 76%][0m
tests/observability/test_vector_drift.py::TestDriftCheckRuntime::test_qdrant_unindexed_collection_is_not_benchmark_ready [32mPASSED[0m[32m [ 82%][0m
tests/observability/test_vector_drift.py::TestDriftCheckRuntime::test_qdrant_with_vectors_is_benchmark_ready [32mPASSED[0m[32m [ 88%][0m
tests/observability/test_vector_drift.py::TestDriftCheckRuntime::test_run_drift_check_reuses_one_embedder_for_all_benchmarks [32mPASSED[0m[32m [ 94%][0m
tests/observability/test_vector_drift.py::TestDriftCheckRuntime::test_run_drift_check_skips_cosine_when_benchmark_is_critical [32mPASSED[0m[32m [100%][0m

================================ tests coverage ================================
_______________ coverage: platform darwin, python 3.11.5-final-0 _______________

Name                                                Stmts   Miss  Cover   Missing
---------------------------------------------------------------------------------
src/__init__.py                                         0      0   100%
src/api/__init__.py                                     0      0   100%
src/api/logging_config.py                              57     57     0%   6-121
src/api/main.py                                      1265   1265     0%   6-2489
src/audit/__init__.py                                 341    341     0%   8-665
src/audit/db_cosign.py                                163    163     0%   17-402
src/audit/per_user_keys.py                            112    112     0%   17-212
src/auth/__init__.py                                    2      2     0%   3-5
src/auth/jwt_handler.py                               152    152     0%   3-345
src/auth/middleware.py                                101    101     0%   3-253
src/auth/rbac.py                                      294    294     0%   17-574
src/auth/refresh_store.py                              65     65     0%   3-151
src/caching/__init__.py                                 0      0   100%
src/caching/redis_layer.py                             64     64     0%   1-108
src/config/__init__.py                                  2      2     0%   3-14
src/config/database.py                                189    189     0%   9-295
src/config/llm_config.py                              854    854     0%   3-1575
src/config/local_llm.py                               232    232     0%   7-421
src/data/__init__.py                                    0      0   100%
src/data/database.py                                   80     80     0%   3-171
src/data/database_v2.py                               397    397     0%   7-873
src/data/metadata/__init__.py                           0      0   100%
src/data/metadata/access_control_labels.py             66     66     0%   6-219
src/db/__init__.py                                      0      0   100%
src/db/seed.py                                         24     24     0%   3-43
src/observability/langfuse_tracer.py                  246    210    15%   29-47, 51, 57-100, 111-168, 173-206, 211-243, 248-281, 292-307, 312-326, 340-347, 350-361, 364-368, 372-376, 380-393, 397-409, 413-415, 427
src/orchestration/__init__.py                           0      0   100%
src/orchestration/checkpoint.py                       102    102     0%   3-187
src/orchestration/graph.py                            160    160     0%   3-256
src/orchestration/nodes/__init__.py                     0      0   100%
src/orchestration/nodes/complexity_classifier.py       71     71     0%   15-180
src/orchestration/nodes/executor.py                   216    216     0%   3-375
src/orchestration/nodes/planner.py                    282    282     0%   3-578
src/orchestration/nodes/receiver.py                    40     40     0%   3-74
src/orchestration/nodes/reflector.py                   27     27     0%   7-78
src/orchestration/nodes/retry_handler.py               31     31     0%   7-80
src/orchestration/nodes/router.py                     398    398     0%   20-921
src/orchestration/nodes/synthesizer.py                655    655     0%   3-1297
src/orchestration/nodes/verifier.py                   279    279     0%   3-570
src/orchestration/state.py                             85     85     0%   3-125
src/orchestration/workflows/__init__.py                 0      0   100%
src/orchestration/workflows/multi_hop.py               21     21     0%   22-76
src/security/__init__.py                                0      0   100%
src/security/dpdp_compliance.py                        70     70     0%   8-181
src/security/egress_guard/__init__.py                 139    139     0%   14-242
src/security/gateway/__init__.py                        0      0   100%
src/security/gateway/prompt_sanitiser.py              145    145     0%   1-515
src/security/headers.py                                38     38     0%   11-85
src/security/pii/__init__.py                           49     49     0%   3-110
src/security/pii/fpe_engine.py                         60     60     0%   1-130
src/security/pii/presidio_config.py                   103    103     0%   3-224
src/security/pii/tokenizer.py                          72     72     0%   1-177
src/security/pii/verhoeff.py                           16     16     0%   8-69
src/security/pii_encryption.py                        102    102     0%   8-170
src/security/query_allowlist.py                        59     59     0%   9-171
src/security/rate_limiter.py                          124    124     0%   14-285
src/security/rbac/__init__.py                           0      0   100%
src/security/rbac/middleware.py                        30     30     0%   7-120
src/security/rbac/postgresql_rbac.py                  102    102     0%   7-326
src/security/rbac/qdrant_rbac.py                      102    102     0%   7-251
src/security/request_signer.py                         57     57     0%   8-150
src/security/security_harden.py                         8      8     0%   16-24
src/security/token_rotation.py                         60     60     0%   9-191
src/skills/__init__.py                                  0      0   100%
src/skills/rag/__init__.py                              2      0   100%
src/skills/rag/embedder.py                            191    155    19%   30-31, 35-61, 65-67, 71, 75-82, 96, 99-117, 120, 127-131, 135-173, 177-210, 214-217, 221-235, 239, 243, 247-249, 253-257, 260, 265-282, 285
src/skills/rag/ingest.py                               68     68     0%   3-121
src/skills/rag/reranker.py                             38     38     0%   3-57
src/skills/rag/retriever.py                           245    210    14%   40-50, 62-94, 103-124, 128-132, 136-148, 152-154, 173-189, 193, 202-218, 225-231, 247-341, 355-367, 375-382, 385-403, 409-410, 414-419, 423-431, 435-493, 497-533, 536, 541-543, 547
src/skills/rag/skill.py                                80     63    21%   20-21, 25-36, 47-82, 86-109, 113-115, 125-126, 131-147, 151
src/skills/text_to_sql/__init__.py                      0      0   100%
src/skills/text_to_sql/sandbox.py                      74     74     0%   3-170
src/skills/text_to_sql/schema_extractor.py            144    144     0%   7-411
src/skills/text_to_sql/schema_sync_check.py           199    199     0%   7-390
src/skills/text_to_sql/skill.py                       555    555     0%   3-1138
src/skills/text_to_sql/sql_examples.py                 29     29     0%   13-340
src/skills/text_to_sql/sql_oracle.py                  152    152     0%   17-322
src/skills/text_to_sql/sqlite_sandbox.py               57     57     0%   3-128
src/skills/text_to_sql/sqlite_schema_extractor.py     120    120     0%   3-418
src/skills/text_to_sql/table_relationships.py          35     35     0%   7-633
src/skills/text_to_sql/validator.py                   136    136     0%   3-329
src/training/__init__.py                                5      5     0%   3-12
src/training/data_collector.py                        164    164     0%   7-375
src/training/data_formatter.py                        119    119     0%   9-248
src/training/export.py                                 78     78     0%   6-171
src/training/quality_filter.py                        103    103     0%   7-180
src/training/stratified_sampler.py                    152    152     0%   14-254
src/utils/__init__.py                                   0      0   100%
src/utils/helpers.py                                   32     32     0%   6-63
src/utils/logging_config.py                            40     40     0%   6-87
---------------------------------------------------------------------------------
TOTAL                                               11227  11101     1%
Coverage XML written to file coverage.xml
[32m============================== [32m[1m17 passed[0m[32m in 2.69s[0m[32m ==============================[0m

7. PII COMPLIANCE:
/Users/srujansai/Desktop/NRG/.venv/lib/python3.11/site-packages/pytest_asyncio/plugin.py:247: PytestDeprecationWarning: The configuration option "asyncio_default_fixture_loop_scope" is unset.
The event loop scope for asynchronous fixtures will default to the fixture caching scope. Future versions of pytest-asyncio will default the loop scope for asynchronous fixtures to function scope. Set the default fixture loop scope explicitly in order to avoid unexpected behavior in the future. Valid fixture loop scopes are: "function", "class", "module", "package", "session"

  warnings.warn(PytestDeprecationWarning(_DEFAULT_FIXTURE_LOOP_SCOPE_UNSET))
[1m============================= test session starts ==============================[0m
platform darwin -- Python 3.11.5, pytest-8.2.2, pluggy-1.6.0 -- /Users/srujansai/Desktop/NRG/.venv/bin/python
cachedir: .pytest_cache
rootdir: /Users/srujansai/Desktop/NRG
configfile: pytest.ini
plugins: cov-7.1.0, Faker-22.6.0, xdist-3.8.0, langsmith-0.7.32, asyncio-1.3.0, anyio-4.13.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
[1mcollecting ... [0mcollected 8 items

tests/security/test_pii_compliance.py::TestPIICompliance::test_aadhaar_detection [32mPASSED[0m[32m [ 12%][0m
tests/security/test_pii_compliance.py::TestPIICompliance::test_dpdp_compliance [32mPASSED[0m[32m [ 25%][0m
tests/security/test_pii_compliance.py::TestPIICompliance::test_email_detection [32mPASSED[0m[32m [ 37%][0m
tests/security/test_pii_compliance.py::TestPIICompliance::test_fpe_encryption [32mPASSED[0m[32m [ 50%][0m
tests/security/test_pii_compliance.py::TestPIICompliance::test_pan_detection [32mPASSED[0m[32m [ 62%][0m
tests/security/test_pii_compliance.py::TestPIICompliance::test_phone_detection [32mPASSED[0m[32m [ 75%][0m
tests/security/test_pii_compliance.py::TestPIICompliance::test_pii_tokenization [32mPASSED[0m[32m [ 87%][0m
tests/security/test_pii_compliance.py::TestPIICompliance::test_presidio_analysis [32mPASSED[0m[32m [100%][0m

================================ tests coverage ================================
_______________ coverage: platform darwin, python 3.11.5-final-0 _______________

Name                                                Stmts   Miss  Cover   Missing
---------------------------------------------------------------------------------
src/__init__.py                                         0      0   100%
src/api/__init__.py                                     0      0   100%
src/api/logging_config.py                              57     57     0%   6-121
src/api/main.py                                      1265   1265     0%   6-2489
src/audit/__init__.py                                 341    341     0%   8-665
src/audit/db_cosign.py                                163    163     0%   17-402
src/audit/per_user_keys.py                            112    112     0%   17-212
src/auth/__init__.py                                    2      2     0%   3-5
src/auth/jwt_handler.py                               152    152     0%   3-345
src/auth/middleware.py                                101    101     0%   3-253
src/auth/rbac.py                                      294    294     0%   17-574
src/auth/refresh_store.py                              65     65     0%   3-151
src/caching/__init__.py                                 0      0   100%
src/caching/redis_layer.py                             64     64     0%   1-108
src/config/__init__.py                                  2      2     0%   3-14
src/config/database.py                                189    189     0%   9-295
src/config/llm_config.py                              854    854     0%   3-1575
src/config/local_llm.py                               232    232     0%   7-421
src/data/__init__.py                                    0      0   100%
src/data/database.py                                   80     80     0%   3-171
src/data/database_v2.py                               397    397     0%   7-873
src/data/metadata/__init__.py                           0      0   100%
src/data/metadata/access_control_labels.py             66     66     0%   6-219
src/db/__init__.py                                      0      0   100%
src/db/seed.py                                         24     24     0%   3-43
src/orchestration/__init__.py                           0      0   100%
src/orchestration/checkpoint.py                       102    102     0%   3-187
src/orchestration/graph.py                            160    160     0%   3-256
src/orchestration/nodes/__init__.py                     0      0   100%
src/orchestration/nodes/complexity_classifier.py       71     71     0%   15-180
src/orchestration/nodes/executor.py                   216    216     0%   3-375
src/orchestration/nodes/planner.py                    282    282     0%   3-578
src/orchestration/nodes/receiver.py                    40     40     0%   3-74
src/orchestration/nodes/reflector.py                   27     27     0%   7-78
src/orchestration/nodes/retry_handler.py               31     31     0%   7-80
src/orchestration/nodes/router.py                     398    398     0%   20-921
src/orchestration/nodes/synthesizer.py                655    655     0%   3-1297
src/orchestration/nodes/verifier.py                   279    279     0%   3-570
src/orchestration/state.py                             85     85     0%   3-125
src/orchestration/workflows/__init__.py                 0      0   100%
src/orchestration/workflows/multi_hop.py               21     21     0%   22-76
src/security/__init__.py                                0      0   100%
src/security/dpdp_compliance.py                        70     70     0%   8-181
src/security/egress_guard/__init__.py                 139    139     0%   14-242
src/security/gateway/__init__.py                        0      0   100%
src/security/gateway/prompt_sanitiser.py              145    145     0%   1-515
src/security/headers.py                                38     38     0%   11-85
src/security/pii/__init__.py                           49     34    31%   29-34, 38-53, 57-89, 94-103
src/security/pii/fpe_engine.py                         60     13    78%   36-45, 54, 71, 100, 116, 121, 126
src/security/pii/presidio_config.py                   103     41    60%   26, 31-33, 51-52, 58, 60-61, 110, 134-144, 147-150, 153-170, 177-178, 181-195, 202-203, 206-220, 224
src/security/pii/tokenizer.py                          72     10    86%   23, 126-130, 140-148
src/security/pii/verhoeff.py                           16     12    25%   42-49, 61-69
src/security/pii_encryption.py                        102    102     0%   8-170
src/security/query_allowlist.py                        59     59     0%   9-171
src/security/rate_limiter.py                          124    124     0%   14-285
src/security/rbac/__init__.py                           0      0   100%
src/security/rbac/middleware.py                        30     30     0%   7-120
src/security/rbac/postgresql_rbac.py                  102    102     0%   7-326
src/security/rbac/qdrant_rbac.py                      102    102     0%   7-251
src/security/request_signer.py                         57     57     0%   8-150
src/security/security_harden.py                         8      8     0%   16-24
src/security/token_rotation.py                         60     60     0%   9-191
src/skills/__init__.py                                  0      0   100%
src/skills/rag/__init__.py                              2      2     0%   3-5
src/skills/rag/embedder.py                            191    191     0%   3-285
src/skills/rag/ingest.py                               68     68     0%   3-121
src/skills/rag/reranker.py                             38     38     0%   3-57
src/skills/rag/retriever.py                           245    245     0%   3-547
src/skills/rag/skill.py                                80     80     0%   3-151
src/skills/text_to_sql/__init__.py                      0      0   100%
src/skills/text_to_sql/sandbox.py                      74     74     0%   3-170
src/skills/text_to_sql/schema_extractor.py            144    144     0%   7-411
src/skills/text_to_sql/schema_sync_check.py           199    199     0%   7-390
src/skills/text_to_sql/skill.py                       555    555     0%   3-1138
src/skills/text_to_sql/sql_examples.py                 29     29     0%   13-340
src/skills/text_to_sql/sql_oracle.py                  152    152     0%   17-322
src/skills/text_to_sql/sqlite_sandbox.py               57     57     0%   3-128
src/skills/text_to_sql/sqlite_schema_extractor.py     120    120     0%   3-418
src/skills/text_to_sql/table_relationships.py          35     35     0%   7-633
src/skills/text_to_sql/validator.py                   136    136     0%   3-329
src/training/__init__.py                                5      5     0%   3-12
src/training/data_collector.py                        164    164     0%   7-375
src/training/data_formatter.py                        119    119     0%   9-248
src/training/export.py                                 78     78     0%   6-171
src/training/quality_filter.py                        103    103     0%   7-180
src/training/stratified_sampler.py                    152    152     0%   14-254
src/utils/__init__.py                                   0      0   100%
src/utils/helpers.py                                   32     32     0%   6-63
src/utils/logging_config.py                            40     40     0%   6-87
---------------------------------------------------------------------------------
TOTAL                                               10981  10791     2%
Coverage XML written to file coverage.xml
[32m============================== [32m[1m8 passed[0m[32m in 10.08s[0m[32m ==============================[0m
