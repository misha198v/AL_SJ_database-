-- Run the ENTIRE file as the owner after all Task 3 files and team seeds.
-- Changes and audit rows are rolled back. On an error, run ROLLBACK;.
BEGIN;
SET LOCAL ROLE alsj_data_entry_staff;
SET LOCAL app.current_user_id = '10000000-0000-0000-0000-000000000002';

-- Allowed: safe user columns and the two views, even with Client RLS enabled.
SELECT user_id, full_name, phone FROM public.users;
SELECT * FROM public.v_document_review_queue;
SELECT * FROM public.rpt_time_per_stage;
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM public.v_document_review_queue
        WHERE document_id = '30000000-0000-0000-0000-000000000002') THEN
        RAISE EXCEPTION 'FAIL: role cannot see its pending review work';
    END IF;
    BEGIN
        PERFORM password_hash FROM public.users LIMIT 1;
        RAISE EXCEPTION 'FAIL: password_hash was readable';
    EXCEPTION WHEN insufficient_privilege THEN
        RAISE NOTICE 'PASS: password_hash SELECT refused';
    END;
    BEGIN
        UPDATE public.applications SET client_id = client_id
        WHERE application_id = '20000000-0000-0000-0000-000000000001';
        RAISE EXCEPTION 'FAIL: direct application changes allowed';
    EXCEPTION WHEN insufficient_privilege THEN
        RAISE NOTICE 'PASS: direct application changes refused';
    END;
    BEGIN
        UPDATE public.documents SET file_path = 'tampered.pdf'
        WHERE document_id = '30000000-0000-0000-0000-000000000002';
        RAISE EXCEPTION 'FAIL: unrelated document changes allowed';
    EXCEPTION WHEN insufficient_privilege THEN
        RAISE NOTICE 'PASS: unrelated document changes refused';
    END;
END;
$$;

SELECT public.data_entry_decide_document(
    '30000000-0000-0000-0000-000000000002', 'VERIFIED', NULL);
SELECT public.data_entry_change_stage(
    '20000000-0000-0000-0000-000000000001',
    (SELECT stage_id::integer FROM public.pipeline_stages WHERE stage_order = 4));

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM public.documents
        WHERE document_id = '30000000-0000-0000-0000-000000000002'
          AND verification_status = 'VERIFIED'
          AND verified_by = '10000000-0000-0000-0000-000000000002') THEN
        RAISE EXCEPTION 'FAIL: document decision did not save Diana as verifier';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM public.stage_history sh JOIN public.pipeline_stages s ON s.stage_id = sh.to_stage_id
        WHERE sh.application_id = '20000000-0000-0000-0000-000000000001'
          AND s.stage_order = 4 AND sh.changed_by = '10000000-0000-0000-0000-000000000002') THEN
        RAISE EXCEPTION 'FAIL: stage movement did not record Diana';
    END IF;
    BEGIN
        PERFORM public.data_entry_decide_document('30000000-0000-0000-0000-000000000002', 'PENDING', NULL);
        RAISE EXCEPTION 'FAIL: non-decision status allowed';
    EXCEPTION WHEN invalid_parameter_value THEN
        RAISE NOTICE 'PASS: only VERIFIED/REJECTED decisions accepted';
    END;
    BEGIN
        PERFORM public.data_entry_decide_document('30000000-0000-0000-0000-000000000002', 'REJECTED', '   ');
        RAISE EXCEPTION 'FAIL: blank rejection reason accepted';
    EXCEPTION WHEN invalid_parameter_value THEN
        RAISE NOTICE 'PASS: blank rejection reason refused';
    END;
    PERFORM public.data_entry_decide_document('30000000-0000-0000-0000-000000000002', 'REJECTED', 'Integration test reason');
    IF NOT EXISTS (SELECT 1 FROM public.documents
        WHERE document_id = '30000000-0000-0000-0000-000000000002'
          AND verification_status = 'REJECTED' AND rejection_reason = 'Integration test reason') THEN
        RAISE EXCEPTION 'FAIL: permitted rejection did not save its reason';
    END IF;
    PERFORM set_config('app.current_user_id', '10000000-0000-0000-0000-000000000001', true);
    BEGIN
        PERFORM public.data_entry_change_stage('20000000-0000-0000-0000-000000000001', 1);
        RAISE EXCEPTION 'FAIL: Field Agent actor accepted by Data Entry routine';
    EXCEPTION WHEN insufficient_privilege THEN
        RAISE NOTICE 'PASS: routine rejects a non-Data-Entry actor';
    END;
END;
$$;
RESET ROLE;
SET LOCAL ROLE alsj_client;
DO $$
BEGIN
    BEGIN
        PERFORM public.data_entry_decide_document('30000000-0000-0000-0000-000000000002', 'VERIFIED', NULL);
        RAISE EXCEPTION 'FAIL: Client can execute privileged Data Entry routine';
    EXCEPTION WHEN insufficient_privilege THEN
        RAISE NOTICE 'PASS: Client cannot execute the privileged routine';
    END;
END;
$$;
RESET ROLE;
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM public.audit_logs
       WHERE entity_id = '30000000-0000-0000-0000-000000000002'
         AND action = 'DOCUMENT_VERIFIED'
         AND user_id = '10000000-0000-0000-0000-000000000002') THEN
        RAISE EXCEPTION 'FAIL: existing document audit trigger was bypassed';
    END IF;
    RAISE NOTICE 'PASS: Data Entry decisions, stage routine, audit integration and restrictions';
END;
$$;
ROLLBACK;

