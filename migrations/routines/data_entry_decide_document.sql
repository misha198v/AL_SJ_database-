-- Task 3 support routine: document decision through a narrow privileged operation.
-- Install as a trusted schema owner, never as the application login.
BEGIN;
CREATE OR REPLACE FUNCTION public.data_entry_decide_document(
    p_document_id UUID, p_decision TEXT, p_rejection_reason TEXT DEFAULT NULL
)
RETURNS UUID
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
    IF p_decision IS NULL OR p_decision NOT IN ('VERIFIED', 'REJECTED') THEN
        RAISE EXCEPTION 'Decision must be VERIFIED or REJECTED' USING ERRCODE = '22023';
    END IF;
    IF p_decision = 'REJECTED' AND (p_rejection_reason IS NULL OR btrim(p_rejection_reason) = '') THEN
        RAISE EXCEPTION 'A rejection reason is required' USING ERRCODE = '22023';
    END IF;
    UPDATE public.documents
    SET verification_status = p_decision::public.verification_status_enum,
        verified_by = v_actor, verified_at = clock_timestamp(),
        rejection_reason = CASE WHEN p_decision = 'REJECTED' THEN p_rejection_reason ELSE NULL END
    WHERE document_id = p_document_id;
    IF NOT FOUND THEN RAISE EXCEPTION 'Document % does not exist', p_document_id USING ERRCODE = 'P0002'; END IF;
    -- Existing verifier-role, validation and audit triggers execute normally.
    RETURN p_document_id;
END;
$$;
REVOKE ALL ON FUNCTION public.data_entry_decide_document(UUID, TEXT, TEXT) FROM PUBLIC;
COMMIT;
