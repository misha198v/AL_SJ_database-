-- Run AFTER seed_amina_documents_payments_appointment.sql, in the same database.
-- Read-only checks; safe after another seed has advanced Amina to Verification.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM public.users u JOIN public.roles r USING (role_id)
        JOIN public.client_profiles cp ON cp.user_id = u.user_id
        WHERE u.user_id = '10000000-0000-0000-0000-000000000011'
          AND u.full_name = 'Amina N.' AND u.email IS NULL AND u.phone = '0772556213'
          AND r.role_name = 'Client' AND cp.national_id = 'CM88213456'
          AND cp.date_of_birth = DATE '1994-05-12' AND cp.address = 'Jinja Road, Kampala'
          AND cp.preferred_language = 'EN'
    ) THEN RAISE EXCEPTION 'FAIL: Amina identity/profile differs from the shared sheet'; END IF;

    IF NOT EXISTS (
        SELECT 1 FROM public.applications
        WHERE application_id = '20000000-0000-0000-0000-000000000001'
          AND client_id = '10000000-0000-0000-0000-000000000011'
          AND assigned_agent_id = '10000000-0000-0000-0000-000000000001'
          AND service_type = 'DOMESTIC_TOURISM' AND destination = 'Jinja'
          AND travel_purpose = 'Family holiday' AND preferred_travel_date = DATE '2026-12-12'
          AND status = 'ACTIVE'
    ) THEN RAISE EXCEPTION 'FAIL: Amina application differs from the shared sheet'; END IF;

    IF NOT EXISTS (
        SELECT 1 FROM public.documents
        WHERE document_id = '30000000-0000-0000-0000-000000000001'
          AND application_id = '20000000-0000-0000-0000-000000000001'
          AND document_type = 'PASSPORT' AND file_path = 'passports/amina_n_passport.pdf'
          AND file_size_bytes = 842000 AND verification_status = 'VERIFIED'
          AND verified_by = '10000000-0000-0000-0000-000000000001'
          AND verified_at = TIMESTAMPTZ '2026-10-06 09:30:00+03' AND rejection_reason IS NULL
    ) THEN RAISE EXCEPTION 'FAIL: verified passport differs from the shared sheet'; END IF;

    IF NOT EXISTS (
        SELECT 1 FROM public.documents
        WHERE document_id = '30000000-0000-0000-0000-000000000002'
          AND application_id = '20000000-0000-0000-0000-000000000001'
          AND document_type = 'NATIONAL_ID' AND file_path = 'ids/amina_n_id.pdf'
          AND file_size_bytes = 310000 AND verification_status = 'PENDING'
          AND verified_by IS NULL AND verified_at IS NULL AND rejection_reason IS NULL
    ) THEN RAISE EXCEPTION 'FAIL: pending national ID differs from the shared sheet'; END IF;

    IF NOT EXISTS (
        SELECT 1 FROM public.payments
        WHERE payment_id = '40000000-0000-0000-0000-000000000001'
          AND application_id = '20000000-0000-0000-0000-000000000001'
          AND amount = 50000 AND currency = 'UGX' AND payment_method = 'MTN_MOMO'
          AND payer_phone = '0772556213' AND status = 'COMPLETED'
          AND transaction_reference = 'MTN-20261003-0001'
          AND initiated_at = TIMESTAMPTZ '2026-10-03 10:00:00+03'
          AND completed_at = TIMESTAMPTZ '2026-10-03 10:02:00+03'
    ) THEN RAISE EXCEPTION 'FAIL: completed payment differs from the shared sheet'; END IF;

    IF NOT EXISTS (
        SELECT 1 FROM public.payments
        WHERE payment_id = '40000000-0000-0000-0000-000000000002'
          AND application_id = '20000000-0000-0000-0000-000000000001'
          AND amount = 20000 AND currency = 'UGX' AND payment_method = 'MTN_MOMO'
          AND payer_phone = '0772556213' AND status = 'PENDING'
          AND transaction_reference IS NULL
          AND initiated_at = TIMESTAMPTZ '2026-10-07 12:00:00+03' AND completed_at IS NULL
    ) THEN RAISE EXCEPTION 'FAIL: pending payment differs from the shared sheet'; END IF;

    IF NOT EXISTS (
        SELECT 1 FROM public.schedule_records
        WHERE schedule_id = '50000000-0000-0000-0000-000000000001'
          AND client_id = '10000000-0000-0000-0000-000000000011'
          AND staff_id = '10000000-0000-0000-0000-000000000003'
          AND appointment_type = 'Document submission'
          AND scheduled_datetime = TIMESTAMPTZ '2026-11-02 10:00:00+03'
          AND status = 'UPCOMING'
    ) THEN RAISE EXCEPTION 'FAIL: appointment differs from the shared sheet'; END IF;

    IF (SELECT count(*) FROM public.documents WHERE application_id = '20000000-0000-0000-0000-000000000001') <> 2
       OR (SELECT count(*) FROM public.payments WHERE application_id = '20000000-0000-0000-0000-000000000001') <> 2
       OR (SELECT count(*) FROM public.schedule_records WHERE client_id = '10000000-0000-0000-0000-000000000011') <> 1 THEN
        RAISE EXCEPTION 'FAIL: expected exactly 2 Amina documents, 2 payments, 1 appointment';
    END IF;
    RAISE NOTICE 'PASS: Amina parents and all five assigned rows match the shared sheet';
END;
$$;
