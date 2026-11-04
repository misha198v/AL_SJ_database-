-- 06_seed_daniel_document_payment_appointment.sql
-- Job 6: Daniel's rejected document, refund and appointment + seed check queries
-- Safe to run alone, in any order, and many times.
-- Column names follow the group data dictionary (design PDF, Section 02).

BEGIN;

-- =====================================================================
-- 1. BASE BLOCK (from seed_base_block.sql)
--    FIX: the original is missing a comma after each phone value in the
--    users INSERT (e.g. '0700000001' <comma> '$2a$10$...'). Added below.
-- =====================================================================
INSERT INTO roles (role_name) VALUES
 ('Client'), ('Field Agent'), ('Data Entry Staff'), ('Secretary'), ('Director')
ON CONFLICT DO NOTHING;

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

-- =====================================================================
-- 2. PARENT ROWS (copied exactly from the sheet)
-- =====================================================================

-- Daniel's user (client role, no email)
INSERT INTO users (user_id, full_name, email, phone, password_hash, role_id) VALUES
 ('10000000-0000-0000-0000-000000000013', 'Daniel O.', NULL, '0700000013',
  '$2a$10$fMn/Zfqq88Ai2E1hJLfhe.rV8Dp4AA0H8xvx5r8NdSs4GhKZpzUEO',
  (SELECT role_id FROM roles WHERE role_name = 'Client'))
ON CONFLICT DO NOTHING;

-- Daniel's client profile
INSERT INTO client_profiles (user_id, national_id, date_of_birth, address, preferred_language) VALUES
 ('10000000-0000-0000-0000-000000000013', 'CM85665544', '1989-11-21', 'Mbarara', 'EN')
ON CONFLICT DO NOTHING;

-- Daniel's application: inserted at stage 1 (Registered) and LEFT there.
-- (Job 5 is the one that moves it to stage 2 after writing the history.)
INSERT INTO applications
 (application_id, client_id, assigned_agent_id, service_type, destination, travel_purpose,
  preferred_travel_date, status, current_stage_id) VALUES
 ('20000000-0000-0000-0000-000000000003',
  '10000000-0000-0000-0000-000000000013',
  '10000000-0000-0000-0000-000000000001',
  'LABOUR_MIGRATION', 'Doha', 'Construction work',
  '2027-02-10', 'CANCELLED',
  (SELECT stage_id FROM pipeline_stages WHERE stage_order = 1))
ON CONFLICT DO NOTHING;

-- =====================================================================
-- 3. MY OWN ROWS (3 rows)
-- =====================================================================

-- 3.1 Rejected document (Diana rejected it on 2026-09-23 15:00 +03)
INSERT INTO documents
 (document_id, application_id, document_type, file_path, file_size_bytes,
  verification_status, verified_by, verified_at, rejection_reason) VALUES
 ('30000000-0000-0000-0000-000000000003',
  '20000000-0000-0000-0000-000000000003',
  'TRAVEL_DECLARATION', 'declarations/daniel_o_decl.pdf', 150000,
  'REJECTED',
  '10000000-0000-0000-0000-000000000002',
  '2026-09-23 15:00:00+03',
  'Signature missing on page 2')
ON CONFLICT DO NOTHING;

-- 3.2 Refunded payment (UGX 15,000, Airtel Money)
INSERT INTO payments
 (payment_id, application_id, amount, currency, payment_method, payer_phone,
  status, transaction_reference, initiated_at, completed_at) VALUES
 ('40000000-0000-0000-0000-000000000004',
  '20000000-0000-0000-0000-000000000003',
  15000, 'UGX', 'AIRTEL_MONEY', '0700000013',
  'REFUNDED', 'AIR20260922-0007',
  '2026-09-22 08:00:00+03', '2026-09-22 08:03:00+03')
ON CONFLICT DO NOTHING;

-- 3.3 Completed initial consultation with Grace (Secretary)
INSERT INTO schedule_records
 (schedule_id, client_id, staff_id, appointment_type, scheduled_datetime, status) VALUES
 ('50000000-0000-0000-0000-000000000002',
  '10000000-0000-0000-0000-000000000013',
  '10000000-0000-0000-0000-000000000003',
  'Initial consultation', '2026-09-19 15:00:00+03', 'COMPLETED')
ON CONFLICT DO NOTHING;

COMMIT;

-- =====================================================================
-- 4. SEED CHECK QUERIES (run AFTER all six files; not part of the seed)
-- =====================================================================

-- 4.1 Row counts per table. Expected:
--   users 7, staff_profiles 4, client_profiles 3, roles 5, pipeline_stages 7,
--   applications 3, stage_history 6, documents 3, payments 4,
--   schedule_records 2, notifications 3, audit_logs 2
SELECT 'users'            AS table_name, COUNT(*) AS row_count, 7 AS expected FROM users
UNION ALL SELECT 'staff_profiles',  COUNT(*), 4 FROM staff_profiles
UNION ALL SELECT 'client_profiles', COUNT(*), 3 FROM client_profiles
UNION ALL SELECT 'roles',           COUNT(*), 5 FROM roles
UNION ALL SELECT 'pipeline_stages', COUNT(*), 7 FROM pipeline_stages
UNION ALL SELECT 'applications',    COUNT(*), 3 FROM applications
UNION ALL SELECT 'stage_history',   COUNT(*), 6 FROM stage_history
UNION ALL SELECT 'documents',       COUNT(*), 3 FROM documents
UNION ALL SELECT 'payments',        COUNT(*), 4 FROM payments
UNION ALL SELECT 'schedule_records',COUNT(*), 2 FROM schedule_records
UNION ALL SELECT 'notifications',   COUNT(*), 3 FROM notifications
UNION ALL SELECT 'audit_logs',      COUNT(*), 2 FROM audit_logs;

-- 4.2 Each application's current stage must equal the to-stage of its
--     LAST history row. This should return ZERO rows.
SELECT a.application_id,
       a.current_stage_id AS current_stage,
       last_h.to_stage_id AS last_history_to_stage
FROM applications a
LEFT JOIN LATERAL (
    SELECT h.to_stage_id
    FROM stage_history h
    WHERE h.application_id = a.application_id
    ORDER BY h.changed_at DESC, h.history_id DESC
    LIMIT 1
) last_h ON TRUE
WHERE a.current_stage_id IS DISTINCT FROM last_h.to_stage_id;

-- 4.3 (Bonus) Same check, readable: shows stage_order for all 3 applications.
SELECT a.application_id, ps.stage_order AS current_stage_order, ps.stage_name
FROM applications a
JOIN pipeline_stages ps ON ps.stage_id = a.current_stage_id
ORDER BY a.application_id;
-- Expected: ...0001 -> 3, ...0002 -> 1, ...0003 -> 2