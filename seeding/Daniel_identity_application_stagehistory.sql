-- 1. Temporarily disable the automatic history trigger
ALTER TABLE applications DISABLE TRIGGER trg_applications_initial_history;

-- 2. Clear out Daniel's current application & history so we can re-seed cleanly
DELETE FROM stage_history WHERE application_id = '20000000-0000-0000-0000-000000000003';
DELETE FROM applications WHERE application_id = '20000000-0000-0000-0000-000000000003';

-- 3. Run Daniel's Job 5 seed script now
BEGIN;

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

INSERT INTO users (user_id, full_name, email, phone, password_hash, role_id) VALUES
('10000000-0000-0000-0000-000000000013', 'Daniel O.', NULL, '0700000013',
 '$2a$10$fMn/Zfqq88Ai2E1hJLfhe.rV8Dp4AA0H8xvx5r8NdSs4GhKZpzUEO',
 (SELECT role_id FROM roles WHERE role_name = 'Client'))
ON CONFLICT DO NOTHING;

INSERT INTO client_profiles (user_id, national_id, date_of_birth, address, preferred_language) VALUES
('10000000-0000-0000-0000-000000000013', 'CM85665544', '1989-11-21', 'Mbarara', 'EN')
ON CONFLICT DO NOTHING;

INSERT INTO applications (
    application_id, client_id, assigned_agent_id, service_type, destination, 
    travel_purpose, preferred_travel_date, status, current_stage_id
) VALUES (
    '20000000-0000-0000-0000-000000000003',
    '10000000-0000-0000-0000-000000000013',
    '10000000-0000-0000-0000-000000000001',
    'LABOUR_MIGRATION',
    'Doha',
    'Construction work',
    '2027-02-10',
    'CANCELLED',
    (SELECT stage_id FROM pipeline_stages WHERE stage_order = 1)
)
ON CONFLICT DO NOTHING;

INSERT INTO stage_history (application_id, from_stage_id, to_stage_id, changed_by, created_at)
SELECT 
    '20000000-0000-0000-0000-000000000003',
    NULL,
    (SELECT stage_id FROM pipeline_stages WHERE stage_order = 1),
    NULL,
    '2026-09-20 09:00:00+03'
WHERE NOT EXISTS (
    SELECT 1 FROM stage_history 
    WHERE application_id = '20000000-0000-0000-0000-000000000003' 
      AND created_at = '2026-09-20 09:00:00+03'
);

INSERT INTO stage_history (application_id, from_stage_id, to_stage_id, changed_by, created_at)
SELECT 
    '20000000-0000-0000-0000-000000000003',
    (SELECT stage_id FROM pipeline_stages WHERE stage_order = 1),
    (SELECT stage_id FROM pipeline_stages WHERE stage_order = 2),
    '10000000-0000-0000-0000-000000000001',
    '2026-09-21 10:00:00+03'
WHERE NOT EXISTS (
    SELECT 1 FROM stage_history 
    WHERE application_id = '20000000-0000-0000-0000-000000000003' 
      AND created_at = '2026-09-21 10:00:00+03'
);

UPDATE applications 
SET current_stage_id = (SELECT stage_id FROM pipeline_stages WHERE stage_order = 2)
WHERE application_id = '20000000-0000-0000-0000-000000000003';

COMMIT;

-- 4. Re-enable the automatic trigger for normal app usage
ALTER TABLE applications ENABLE TRIGGER trg_applications_initial_history;