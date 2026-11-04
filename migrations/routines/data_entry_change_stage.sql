-- Task 3 support routine: use the existing transactional stage-change function.
-- Install as a trusted schema owner, never as the application login.
BEGIN;
CREATE OR REPLACE FUNCTION public.data_entry_change_stage(p_application_id UUID, p_new_stage_id INTEGER)
RETURNS BIGINT
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, public, pg_temp
AS $$
DECLARE
    v_actor UUID := NULLIF(current_setting('app.current_user_id', true), '')::uuid;
BEGIN
    PERFORM 1 FROM public.users u
    JOIN public.roles r ON r.role_id = u.role_id
    WHERE u.user_id = v_actor AND r.role_name = 'Data Entry Staff' AND u.is_active
    FOR SHARE OF u, r;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'An active Data Entry Staff actor must be set in app.current_user_id'
            USING ERRCODE = '42501';
    END IF;
    IF p_new_stage_id IS NULL OR NOT EXISTS (
        SELECT 1 FROM public.pipeline_stages WHERE stage_id = p_new_stage_id
    ) THEN
        RAISE EXCEPTION 'A valid destination stage is required' USING ERRCODE = '22023';
    END IF;
    -- Delegates row locking, current_stage update and history insert to the team routine.
    RETURN public.change_stage(p_application_id, p_new_stage_id, v_actor);
END;
$$;
REVOKE ALL ON FUNCTION public.data_entry_change_stage(UUID, INTEGER) FROM PUBLIC;
COMMIT;
