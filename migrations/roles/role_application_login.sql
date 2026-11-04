-- =========================================================================
-- Description: Creates the application login role, revokes default public 
--              rights, and provisions least-privilege connection rights.
-- =========================================================================

-- 1. Create the application login role (Replace 'SecureAppPassword123!' with a secure environment secret)
CREATE ROLE app_user WITH LOGIN PASSWORD 'SecureAppPassword123!';

-- 2. Remove default public privileges from the database schema
REVOKE ALL ON DATABASE alsj_travelagency_local FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM PUBLIC;

-- 3. Grant connection and usage rights to the application login role
GRANT CONNECT ON DATABASE alsj_travelagency_local TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;

-- 4. Grant appropriate table-level permissions (Adjust based on your runtime needs)
-- The application typically needs DML access to core operational tables
GRANT SELECT, INSERT, UPDATE ON applications, documents, payments, schedule_records, notifications, audit_logs, stage_history TO app_user;
GRANT SELECT ON roles, pipeline_stages, client_profiles, staff_profiles, users TO app_user;

-- 5. Grant usage on sequences for auto-incrementing keys (like BIGSERIAL / SMALLSERIAL)
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;