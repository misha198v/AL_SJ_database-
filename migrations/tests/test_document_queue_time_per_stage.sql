-- Run as the database owner on the team's seeded development database.
-- Hand-count checks for six seeded history rows, followed by rolled-back edge fixtures.
DO $$
BEGIN
    IF to_regclass('public.v_document_review_queue') IS NULL THEN
        RAISE EXCEPTION 'FAIL: document queue view is missing';
    END IF;
    IF to_regclass('public.rpt_time_per_stage') IS NULL THEN
        RAISE EXCEPTION 'FAIL: time-per-stage report is missing';
    END IF;
    IF (SELECT count(*) FROM public.v_document_review_queue) <> 1
       OR NOT EXISTS (SELECT 1 FROM public.v_document_review_queue
          WHERE document_id = '30000000-0000-0000-0000-000000000002'
            AND client_name = 'Amina N.' AND document_type = 'NATIONAL_ID' AND destination = 'Jinja') THEN
        RAISE EXCEPTION 'FAIL: seeded queue should contain only Amina national ID';
    END IF;
    IF (SELECT count(*) FROM public.rpt_time_per_stage) <> 6 THEN
        RAISE EXCEPTION 'FAIL: expected six seeded stage visits';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM public.rpt_time_per_stage
        WHERE application_id = '20000000-0000-0000-0000-000000000001'
          AND stage_order = 1 AND time_in_stage = INTERVAL '25 hours'
          AND average_time_in_stage = INTERVAL '25 hours' AND completed_visit_count = 2) THEN
        RAISE EXCEPTION 'FAIL: Registered time/average should be 25 hours (two completed visits)';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM public.rpt_time_per_stage
        WHERE application_id = '20000000-0000-0000-0000-000000000001'
          AND stage_order = 2 AND time_in_stage = INTERVAL '73 hours'
          AND average_time_in_stage = INTERVAL '73 hours' AND completed_visit_count = 1) THEN
        RAISE EXCEPTION 'FAIL: Amina Docs Pending time/average should be 73 hours';
    END IF;
    IF (SELECT count(*) FROM public.rpt_time_per_stage WHERE exited_at IS NULL AND time_in_stage IS NULL) <> 3 THEN
        RAISE EXCEPTION 'FAIL: three ongoing visits must have no completed duration';
    END IF;
    RAISE NOTICE 'PASS: seeded document queue and stage durations/averages match hand counts';
END;
$$;

-- Edge checks: oldest-first queue, equal history timestamps and a repeat stage visit.
-- Real fixtures are rolled back, leaving the original seeded dataset unchanged.
BEGIN;
DO $$
DECLARE
    stage_two SMALLINT := (SELECT stage_id FROM public.pipeline_stages WHERE stage_order = 2);
    stage_three SMALLINT := (SELECT stage_id FROM public.pipeline_stages WHERE stage_order = 3);
    first_doc UUID := gen_random_uuid();
    second_doc UUID := gen_random_uuid();
    actual_order UUID[];
BEGIN
    INSERT INTO public.documents (document_id, application_id, document_type, file_path, file_size_bytes, uploaded_at)
    VALUES (second_doc, '20000000-0000-0000-0000-000000000001', 'PASSPORT', 'test-newer.pdf', 100, '2000-01-02 00:00+03'),
           (first_doc, '20000000-0000-0000-0000-000000000001', 'PASSPORT', 'test-older.pdf', 100, '2000-01-01 00:00+03');
    actual_order := ARRAY(SELECT document_id FROM public.v_document_review_queue LIMIT 2);
    IF actual_order IS DISTINCT FROM ARRAY[first_doc, second_doc] THEN
        RAISE EXCEPTION 'FAIL: queue is not ordered oldest first';
    END IF;
    INSERT INTO public.stage_history (application_id, from_stage_id, to_stage_id, changed_at)
    VALUES ('20000000-0000-0000-0000-000000000001', stage_three, stage_two, '2026-10-06 11:00+03');
    INSERT INTO public.stage_history (application_id, from_stage_id, to_stage_id, changed_at)
    VALUES ('20000000-0000-0000-0000-000000000001', stage_two, stage_three, '2026-10-06 11:00+03');
    IF NOT EXISTS (SELECT 1 FROM public.rpt_time_per_stage
        WHERE application_id = '20000000-0000-0000-0000-000000000001' AND stage_order = 2
          AND entered_at = TIMESTAMPTZ '2026-10-06 11:00+03' AND time_in_stage = INTERVAL '0'
          AND average_time_in_stage = INTERVAL '36 hours 30 minutes' AND completed_visit_count = 2) THEN
        RAISE EXCEPTION 'FAIL: repeated stage visits/tied timestamps averaged incorrectly';
    END IF;
    RAISE NOTICE 'PASS: queue ordering, repeated visits and equal-timestamp tie handling';
END;
$$;
ROLLBACK;

