-- Job 2 only: Amina's documents, payments and appointment (five owned rows).
-- Source: SEEDING POLL.pdf and seed base block.pdf.
-- Fixed shared UUIDs; safe to repeat. Run the ENTIRE file in the project database.
-- Do not change Amina's stage/history here: those belong to Job 1.
BEGIN;

-- seed_base_block.sql
-- Paste this block at the top of EVERY seed file, right after BEGIN;
-- It is safe to run many times: ON CONFLICT DO NOTHING skips rows that already exist.
-- 20 rows: 5 roles, 7 pipeline stages, 4 staff users, 4 staff profiles.
-- Demo password for every seeded user: ChangeMe123!  (bcrypt hash below, development only)
INSERT INTO roles (role_name) VALUES
    ('Client'), ('Field Agent'), ('Data Entry Staff'), ('Secretary'), ('Director')
ON CONFLICT DO NOTHING;
-- The sixth role is still to be confirmed (PDF p.2 and p.5). Add it here when decided.
INSERT INTO pipeline_stages (stage_name, stage_order) VALUES
    ('Registered', 1), ('Docs Pending', 2), ('Verification', 3), ('Payment', 4),
    ('Processing', 5), ('Ready', 6), ('Departed', 7)
ON CONFLICT DO NOTHING;
INSERT INTO users (user_id, full_name, email, phone, password_hash, role_id) VALUES
    ('10000000-0000-0000-0000-000000000001', 'Brian K.', 'brian.k@alsj.example', '0700000001',
     '$2a$10$fMn/Zfqq88Ai2E1hJLfhe.rV8Dp4AA0H8xvx5r8NdSs4GhKZpzUEO',
     (SELECT role_id FROM roles WHERE role_name = 'Field Agent')),
    ('10000000-0000-0000-0000-000000000002', 'Diana S.', 'diana.s@alsj.example', '0700000002',
     '$2a$10$fMn/Zfqq88Ai2E1hJLfhe.rV8Dp4AA0H8xvx5r8NdSs4GhKZpzUEO',
     (SELECT role_id FROM roles WHERE role_name = 'Data Entry Staff')),
    ('10000000-0000-0000-0000-000000000003', 'Grace T.', 'grace.t@alsj.example', '0700000003',
     '$2a$10$fMn/Zfqq88Ai2E1hJLfhe.rV8Dp4AA0H8xvx5r8NdSs4GhKZpzUEO',
     (SELECT role_id FROM roles WHERE role_name = 'Secretary')),
    ('10000000-0000-0000-0000-000000000004', 'Moses L.', 'moses.l@alsj.example', '0700000004',
     '$2a$10$fMn/Zfqq88Ai2E1hJLfhe.rV8Dp4AA0H8xvx5r8NdSs4GhKZpzUEO',
     (SELECT role_id FROM roles WHERE role_name = 'Director'))
ON CONFLICT DO NOTHING;
INSERT INTO staff_profiles (user_id, employee_no, date_hired) VALUES
    ('10000000-0000-0000-0000-000000000001', 'ALSJ-001', '2024-03-01'),
    ('10000000-0000-0000-0000-000000000002', 'ALSJ-002', '2024-06-15'),
    ('10000000-0000-0000-0000-000000000003', 'ALSJ-003', '2025-01-10'),
    ('10000000-0000-0000-0000-000000000004', 'ALSJ-004', '2023-09-01')
ON CONFLICT DO NOTHING;

-- Required parent rows, shared with Amina's identity/application owner.
INSERT INTO users (user_id, full_name, email, phone, password_hash, role_id)
VALUES (
    '10000000-0000-0000-0000-000000000011', 'Amina N.', NULL, '0772556213',
    '$2a$10$fMn/Zfqq88Ai2E1hJLfhe.rV8Dp4AA0H8xvx5r8NdSs4GhKZpzUEO',
    (SELECT role_id FROM roles WHERE role_name = 'Client')
)
ON CONFLICT DO NOTHING;

INSERT INTO client_profiles (user_id, national_id, date_of_birth, address, preferred_language)
VALUES ('10000000-0000-0000-0000-000000000011', 'CM88213456', '1994-05-12', 'Jinja Road, Kampala', 'EN')
ON CONFLICT DO NOTHING;

-- Copied parent starts at Registered; do not reset an application Job 1 advanced.
INSERT INTO applications (
    application_id, client_id, assigned_agent_id, current_stage_id,
    service_type, destination, travel_purpose, preferred_travel_date, status
)
VALUES (
    '20000000-0000-0000-0000-000000000001',
    '10000000-0000-0000-0000-000000000011',
    '10000000-0000-0000-0000-000000000001',
    (SELECT stage_id FROM pipeline_stages WHERE stage_order = 1),
    'DOMESTIC_TOURISM', 'Jinja', 'Family holiday', '2026-12-12', 'ACTIVE'
)
ON CONFLICT DO NOTHING;

-- Own rows 1-2: verified passport and pending national ID.
-- Insert the historical final states directly: Job 3 owns the two shared audit rows.
INSERT INTO documents (
    document_id, application_id, document_type, file_path, file_size_bytes,
    verification_status, verified_by, verified_at, rejection_reason
)
VALUES
    ('30000000-0000-0000-0000-000000000001',
     '20000000-0000-0000-0000-000000000001',
     'PASSPORT', 'passports/amina_n_passport.pdf', 842000, 'VERIFIED',
     '10000000-0000-0000-0000-000000000001', '2026-10-06 09:30:00+03', NULL),
    ('30000000-0000-0000-0000-000000000002',
     '20000000-0000-0000-0000-000000000001',
     'NATIONAL_ID', 'ids/amina_n_id.pdf', 310000, 'PENDING', NULL, NULL, NULL)
ON CONFLICT DO NOTHING;

-- Own rows 3-4: completed UGX 50,000 and pending UGX 20,000, both MTN MoMo.
INSERT INTO payments (
    payment_id, application_id, amount, currency, payment_method, payer_phone,
    transaction_reference, status, initiated_at, completed_at
)
VALUES
    ('40000000-0000-0000-0000-000000000001',
     '20000000-0000-0000-0000-000000000001', 50000, 'UGX', 'MTN_MOMO', '0772556213',
     'MTN-20261003-0001', 'COMPLETED', '2026-10-03 10:00:00+03', '2026-10-03 10:02:00+03'),
    ('40000000-0000-0000-0000-000000000002',
     '20000000-0000-0000-0000-000000000001', 20000, 'UGX', 'MTN_MOMO', '0772556213',
     NULL, 'PENDING', '2026-10-07 12:00:00+03', NULL)
ON CONFLICT DO NOTHING;

-- Own row 5: upcoming document submission with Grace (Secretary with staff profile).
INSERT INTO schedule_records (
    schedule_id, client_id, staff_id, appointment_type, scheduled_datetime, status
)
VALUES (
    '50000000-0000-0000-0000-000000000001',
    '10000000-0000-0000-0000-000000000011',
    '10000000-0000-0000-0000-000000000003',
    'Document submission', '2026-11-02 10:00:00+03', 'UPCOMING'
)
ON CONFLICT DO NOTHING;

COMMIT;
