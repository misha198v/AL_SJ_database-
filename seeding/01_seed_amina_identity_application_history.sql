-- 01_seed_amina_identity_application_history.sql
-- Job 1: Amina's identity, application and stage history
-- Safe to run alone, in any order, and many times.

BEGIN;

-- =====================================================================
-- 1. BASE BLOCK (from seed_base_block.sql, unchanged)
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
-- 2. MY OWN ROWS (6 rows)
-- =====================================================================

-- 2.1 Amina's user (client role, no email)
INSERT INTO users (user_id, full_name, email, phone, password_hash, role_id) VALUES
 ('10000000-0000-0000-0000-000000000011', 'Amina N.', NULL, '0772556213',
  '$2a$10$fMn/Zfqq88Ai2E1hJLfhe.rV8Dp4AA0H8xvx5r8NdSs4GhKZpzUEO',
  (SELECT role_id FROM roles WHERE role_name = 'Client'))
ON CONFLICT DO NOTHING;

-- 2.2 Amina's client profile
INSERT INTO client_profiles (user_id, national_id, date_of_birth, address, preferred_language) VALUES
 ('10000000-0000-0000-0000-000000000011', 'CM88213456', '1994-05-12', 'Jinja Road, Kampala', 'EN')
ON CONFLICT DO NOTHING;

-- 2.3 Amina's application: inserted at stage 1 (Registered)
INSERT INTO applications
 (application_id, client_id, assigned_agent_id, service_type, destination, travel_purpose,
  preferred_travel_date, status, current_stage_id) VALUES
 ('20000000-0000-0000-0000-000000000001',
  '10000000-0000-0000-0000-000000000011',
  '10000000-0000-0000-0000-000000000001',
  'DOMESTIC_TOURISM', 'Jinja', 'Family holiday',
  '2026-12-12', 'ACTIVE',
  (SELECT stage_id FROM pipeline_stages WHERE stage_order = 1))
ON CONFLICT DO NOTHING;

-- 2.4 Stage history, row 1: empty -> 1, by system
INSERT INTO stage_history (application_id, from_stage_id, to_stage_id, changed_by, changed_at)
SELECT '20000000-0000-0000-0000-000000000001', NULL,
       (SELECT stage_id FROM pipeline_stages WHERE stage_order = 1),
       NULL, '2026-10-01 09:00:00+03'
WHERE NOT EXISTS (
  SELECT 1 FROM stage_history
  WHERE application_id = '20000000-0000-0000-0000-000000000001'
    AND changed_at = '2026-10-01 09:00:00+03');

-- 2.5 Stage history, row 2: 1 -> 2, by Brian
INSERT INTO stage_history (application_id, from_stage_id, to_stage_id, changed_by, changed_at)
SELECT '20000000-0000-0000-0000-000000000001',
       (SELECT stage_id FROM pipeline_stages WHERE stage_order = 1),
       (SELECT stage_id FROM pipeline_stages WHERE stage_order = 2),
       '10000000-0000-0000-0000-000000000001', '2026-10-02 10:00:00+03'
WHERE NOT EXISTS (
  SELECT 1 FROM stage_history
  WHERE application_id = '20000000-0000-0000-0000-000000000001'
    AND changed_at = '2026-10-02 10:00:00+03');

-- 2.6 Stage history, row 3: 2 -> 3, by Brian
INSERT INTO stage_history (application_id, from_stage_id, to_stage_id, changed_by, changed_at)
SELECT '20000000-0000-0000-0000-000000000001',
       (SELECT stage_id FROM pipeline_stages WHERE stage_order = 2),
       (SELECT stage_id FROM pipeline_stages WHERE stage_order = 3),
       '10000000-0000-0000-0000-000000000001', '2026-10-05 11:00:00+03'
WHERE NOT EXISTS (
  SELECT 1 FROM stage_history
  WHERE application_id = '20000000-0000-0000-0000-000000000001'
    AND changed_at = '2026-10-05 11:00:00+03');

-- 2.7 Last statement: move the application to stage 3 (Verification)
UPDATE applications
SET current_stage_id = (SELECT stage_id FROM pipeline_stages WHERE stage_order = 3)
WHERE application_id = '20000000-0000-0000-0000-000000000001';

COMMIT;