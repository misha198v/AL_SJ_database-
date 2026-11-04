-- Task 3 database role. Run AFTER the two views and two support routines, as owner.
-- This PostgreSQL permission role is separate from the application's roles table.
BEGIN;
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'alsj_data_entry_staff') THEN
        CREATE ROLE alsj_data_entry_staff NOLOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'alsj_data_entry_staff'
        AND (rolsuper OR rolbypassrls OR rolcreatedb OR rolcreaterole OR rolcanlogin)) THEN
        RAISE EXCEPTION 'Existing alsj_data_entry_staff has unexpected elevated attributes; review it first';
    END IF;
END;
$$;
GRANT USAGE ON SCHEMA public TO alsj_data_entry_staff;
REVOKE ALL ON public.users FROM alsj_data_entry_staff;
REVOKE SELECT (password_hash) ON public.users FROM alsj_data_entry_staff;
GRANT SELECT (user_id, full_name, email, phone, role_id, is_active, created_at, updated_at)
    ON public.users TO alsj_data_entry_staff;
GRANT SELECT ON public.roles, public.applications, public.documents,
    public.pipeline_stages, public.stage_history TO alsj_data_entry_staff;
GRANT SELECT ON public.v_document_review_queue, public.rpt_time_per_stage TO alsj_data_entry_staff;
GRANT EXECUTE ON FUNCTION public.data_entry_decide_document(UUID, TEXT, TEXT),
    public.data_entry_change_stage(UUID, INTEGER) TO alsj_data_entry_staff;

-- The Client role file enables RLS. These role-specific SELECT policies allow
-- Data Entry Staff to review work without changing Client policies or enabling
-- UPDATE/INSERT/DELETE access. They also work if RLS has not been enabled yet.
DROP POLICY IF EXISTS data_entry_read_users ON public.users;
CREATE POLICY data_entry_read_users ON public.users FOR SELECT TO alsj_data_entry_staff USING (true);
DROP POLICY IF EXISTS data_entry_read_applications ON public.applications;
CREATE POLICY data_entry_read_applications ON public.applications FOR SELECT TO alsj_data_entry_staff USING (true);
DROP POLICY IF EXISTS data_entry_read_documents ON public.documents;
CREATE POLICY data_entry_read_documents ON public.documents FOR SELECT TO alsj_data_entry_staff USING (true);
DROP POLICY IF EXISTS data_entry_read_stage_history ON public.stage_history;
CREATE POLICY data_entry_read_stage_history ON public.stage_history FOR SELECT TO alsj_data_entry_staff USING (true);
DROP POLICY IF EXISTS data_entry_read_stages ON public.pipeline_stages;
CREATE POLICY data_entry_read_stages ON public.pipeline_stages FOR SELECT TO alsj_data_entry_staff USING (true);

-- Detect accidental exposure through PUBLIC or a previously granted membership.
DO $$
BEGIN
    IF has_column_privilege('alsj_data_entry_staff', 'public.users', 'password_hash', 'SELECT') THEN
        RAISE EXCEPTION 'password_hash is exposed through PUBLIC or inherited grants; resolve those grants before installing';
    END IF;
END;
$$;
COMMIT;
