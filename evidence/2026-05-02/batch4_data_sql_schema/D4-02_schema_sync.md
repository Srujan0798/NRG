SCHEMA SYNC REPORT
============================================================

⚠️ EXTRA TABLES in live DB (17):
   - alembic_version
   - audit_events
   - collaborations
   - funding
   - funding_records
   - institutions
   - keywords
   - labs
   - llm_cost_log
   - patents
   - projects
   - publication_keywords
   - publications
   - research_documents
   - researcher_labs
   - researcher_publications
   - researchers

⚠️ TYPE MISMATCHES (92 columns):
   auth_group.name: expected CHARACTER, got VARCHAR(150)
   auth_permission.codename: expected CHARACTER, got VARCHAR(100)
   auth_permission.name: expected CHARACTER, got VARCHAR(255)
   auth_user.email: expected CHARACTER, got VARCHAR(254)
   auth_user.first_name: expected CHARACTER, got VARCHAR(150)
   auth_user.last_name: expected CHARACTER, got VARCHAR(150)
   auth_user.password: expected CHARACTER, got VARCHAR(128)
   auth_user.username: expected CHARACTER, got VARCHAR(150)
   django_admin_log.object_repr: expected CHARACTER, got VARCHAR(200)
   django_content_type.app_label: expected CHARACTER, got VARCHAR(100)
   django_content_type.model: expected CHARACTER, got VARCHAR(100)
   django_migrations.app: expected CHARACTER, got VARCHAR(255)
   django_migrations.name: expected CHARACTER, got VARCHAR(255)
   django_session.session_key: expected CHARACTER, got VARCHAR(40)
   expertise.department: expected CHARACTER, got VARCHAR
   expertise.designation: expected CHARACTER, got VARCHAR
   expertise.email: expected CHARACTER, got VARCHAR
   expertise.image: expected CHARACTER, got VARCHAR
   expertise.institute: expected CHARACTER, got VARCHAR
   expertise.name: expected CHARACTER, got VARCHAR
   expertise.phd: expected CHARACTER, got VARCHAR
   expertise.phone: expected CHARACTER, got VARCHAR
   expertise.research: expected CHARACTER, got VARCHAR
   faculty_strength.academic_year: expected CHARACTER, got VARCHAR(10)
   faculty_strength.as_on: expected CHARACTER, got VARCHAR(20)
   faculty_strength.female_strength: expected CHARACTER, got VARCHAR(100)
   faculty_strength.institute: expected CHARACTER, got VARCHAR(100)
   faculty_strength.male_strength: expected CHARACTER, got VARCHAR(100)
   faculty_strength.total_sanctioned_strength: expected CHARACTER, got VARCHAR(100)
   faculty_strength.total_strength: expected CHARACTER, got VARCHAR(100)
   faculty_strength.types: expected CHARACTER, got VARCHAR(100)
   faculty_strength.uploaded_on: expected CHARACTER, got VARCHAR(100)
   faculty_strength.url: expected CHARACTER, got VARCHAR(100)
   master_expertise.department: expected CHARACTER, got VARCHAR
   master_expertise.institute: expected CHARACTER, got VARCHAR
   nirf_extracted_table.title: expected CHARACTER, got VARCHAR(255)
   nirf_pdf_record.institute: expected CHARACTER, got VARCHAR(255)
   nirf_pdf_record.pdf_name: expected CHARACTER, got VARCHAR(255)
   nirf_pdf_record.uploaded_by: expected CHARACTER, got VARCHAR(255)
   nirf_pdf_record.year: expected CHARACTER, got VARCHAR(10)
   package_data.name: expected CHARACTER, got VARCHAR
   package_data.package: expected CHARACTER, got VARCHAR
   package_data.status: expected CHARACTER, got VARCHAR
   role_data.name: expected CHARACTER, got VARCHAR
   role_data.status: expected CHARACTER, got VARCHAR
   seed_funding.achievement_level: expected CHARACTER, got VARCHAR(255)
   seed_funding.as_on_year: expected CHARACTER, got VARCHAR(10)
   seed_funding.dpiit_no: expected CHARACTER, got VARCHAR(100)
   seed_funding.govt_org: expected CHARACTER, got VARCHAR(255)
   seed_funding.institute: expected CHARACTER, got VARCHAR(255)
   seed_funding.startup_name: expected CHARACTER, got VARCHAR(255)
   seed_funding.type_of_investment: expected CHARACTER, got VARCHAR(255)
   seed_funding.year_of_receiving_fund: expected CHARACTER, got VARCHAR(10)
   tb_academic_year_mstr.academic_year: expected CHARACTER, got VARCHAR
   tb_course_program_types.program_name: expected CHARACTER, got VARCHAR
   tb_goi_ministries_mstr.address: expected CHARACTER, got VARCHAR
   tb_goi_ministries_mstr.email: expected CHARACTER, got VARCHAR
   tb_goi_ministries_mstr.name: expected CHARACTER, got VARCHAR
   tb_goi_ministries_mstr.phone_no: expected CHARACTER, got VARCHAR
   tb_goi_ministries_mstr.short_name: expected CHARACTER, got VARCHAR
   tb_goi_ministries_mstr.website: expected CHARACTER, got VARCHAR
   tb_institute_mstr.address: expected CHARACTER, got VARCHAR
   tb_institute_mstr.city: expected CHARACTER, got VARCHAR
   tb_institute_mstr.institute_name: expected CHARACTER, got VARCHAR
   tb_institute_mstr.institute_type: expected CHARACTER, got VARCHAR
   tb_institute_mstr.short_name: expected CHARACTER, got VARCHAR
   tb_institute_mstr.state: expected CHARACTER, got VARCHAR
   tb_institute_mstr.website_url: expected CHARACTER, got VARCHAR
   tb_institute_scrap_data_url.city: expected CHARACTER, got VARCHAR(100)
   tb_institute_scrap_data_url.institute_name: expected CHARACTER, got VARCHAR(255)
   tb_institute_scrap_data_url.institute_type: expected CHARACTER, got VARCHAR(100)
   tb_institute_scrap_data_url.short_name: expected CHARACTER, got VARCHAR(100)
   tb_institute_scrap_data_url.state: expected CHARACTER, got VARCHAR(100)
   user_registration.confirm_password: expected CHARACTER, got VARCHAR(128)
   user_registration.deleted_by: expected CHARACTER, got VARCHAR
   user_registration.email: expected CHARACTER, got VARCHAR(254)
   user_registration.email_otp: expected CHARACTER, got VARCHAR
   user_registration.email_status: expected CHARACTER, got VARCHAR
   user_registration.first_password: expected CHARACTER, got VARCHAR
   user_registration.password: expected CHARACTER, got VARCHAR(128)
   user_registration.phone_number: expected CHARACTER, got VARCHAR(15)
   user_registration.role: expected CHARACTER, got VARCHAR(20)
   user_registration.status: expected CHARACTER, got VARCHAR
   user_registration.user_info: expected CHARACTER, got VARCHAR
   user_registration.username: expected CHARACTER, got VARCHAR(50)
   user_registration_old.confirm_password: expected CHARACTER, got VARCHAR(128)
   user_registration_old.email: expected CHARACTER, got VARCHAR(254)
   user_registration_old.password: expected CHARACTER, got VARCHAR(128)
   user_registration_old.phone_number: expected CHARACTER, got VARCHAR(15)
   user_registration_old.role: expected CHARACTER, got VARCHAR(20)
   user_registration_old.user_info: expected CHARACTER, got VARCHAR
   user_registration_old.username: expected CHARACTER, got VARCHAR(50)
