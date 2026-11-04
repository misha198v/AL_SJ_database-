-- create_role_client.sql
-- Role alsj_client: a client sees only their own applications, documents, payments and notifications.
-- Source: PDF p.3 (clients upload, pay and track), p.4-5 (a hard-to-guess id is not a lock:
--         authorization is still required), p.5 (password_hash must stay private)
-- How it works: the application connects with its login role, runs SET ROLE alsj_client and then
--   SET app.current_user_id = '<the client's user_id>';
-- Row-level security compares each row with that id.
-- NOTE: enabling row-level security on a table hides ALL rows from every role (except the table
-- owner) that has no policy of its own. Every other role file must add its own policy.

-- 1. The role (roles belong to the whole server, so create it only if missing)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'alsj_client') THEN
        CREATE ROLE alsj_client NOLOGIN;
    END IF;
END $$;

-- 2. Who is the current client? (empty when the application has not set it)
CREATE OR REPLACE FUNCTION app_current_user_id()
RETURNS uuid
LANGUAGE sql STABLE
AS $$ SELECT NULLIF(current_setting('app.current_user_id', true), '')::uuid $$;

-- 3. What the role may read
GRANT USAGE ON SCHEMA public TO alsj_client;
GRANT EXECUTE ON FUNCTION app_current_user_id() TO alsj_client;
GRANT SELECT ON applications, documents, payments, notifications, pipeline_stages TO alsj_client;
GRANT SELECT (user_id, full_name, phone) ON users TO alsj_client;   -- never password_hash or email
GRANT SELECT ON v_application_overview TO alsj_client;

-- 4. Row-level security: only the client's own rows
ALTER TABLE applications  ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents     ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments      ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE users         ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS client_own_applications  ON applications;
DROP POLICY IF EXISTS client_own_documents     ON documents;
DROP POLICY IF EXISTS client_own_payments      ON payments;
DROP POLICY IF EXISTS client_own_notifications ON notifications;
DROP POLICY IF EXISTS client_own_user_and_agent ON users;

CREATE POLICY client_own_applications ON applications
    FOR SELECT TO alsj_client
    USING (client_id = app_current_user_id());

CREATE POLICY client_own_documents ON documents
    FOR SELECT TO alsj_client
    USING (application_id IN (SELECT application_id FROM applications WHERE client_id = app_current_user_id()));

CREATE POLICY client_own_payments ON payments
    FOR SELECT TO alsj_client
    USING (application_id IN (SELECT application_id FROM applications WHERE client_id = app_current_user_id()));

CREATE POLICY client_own_notifications ON notifications
    FOR SELECT TO alsj_client
    USING (user_id = app_current_user_id());

-- the client's own user row, and the row of their assigned agent (only name and phone are granted)
CREATE POLICY client_own_user_and_agent ON users
    FOR SELECT TO alsj_client
    USING (user_id = app_current_user_id()
           OR user_id IN (SELECT assigned_agent_id FROM applications WHERE client_id = app_current_user_id()));
