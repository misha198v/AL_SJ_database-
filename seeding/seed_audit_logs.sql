-- =========================================================================
-- Seed File: seed_audit_logs.sql
-- Description: Seeds roles, stages, staff, user context, 
--              and the 2 system audit logs.
-- Source: SEEDING POLL.pdf p. 2 & seed_base_block.sql[cite: 51, 54]
-- =========================================================================

BEGIN;

-- 1. Base Block (Roles, Stages, Staff Users & Staff Profiles)[cite: 54]
INSERT INTO roles (role_name) VALUES
('Client'), ('Field Agent'), ('Data Entry Staff'), ('Secretary'), ('Director')
ON CONFLICT DO NOTHING;

INSERT INTO pipeline_stages (stage_name, stage_order) VALUES
('Registered', 1), ('Docs Pending', 2), ('Verification', 3), ('Payment', 4),
('Processing', 5), ('Ready', 6), ('Departed', 7)
ON CONFLICT DO NOTHING;

INSERT INTO users (user_id, full_name, email, phone, password_hash, role_id) VALUES
('10000000-0000-0000-0000-000000000001', 'Brian K.', 'brian.k@alsj.example', '0772000001', '$2a$10$fMn/Zfqq88Ai2ElhJLfhe.rV8Dp4AA0H8xvx5r8NdSs4GhKZpzUEO', (SELECT role_id FROM roles WHERE role_name = 'Field Agent')),
('10000000-0000-0000-0000-000000000002', 'Diana S.', 'diana.s@alsj.example', '0772000002', '$2a$10$fMn/Zfqq88Ai2ElhJLfhe.rV8Dp4AA0H8xvx5r8NdSs4GhKZpzUEO', (SELECT role_id FROM roles WHERE role_name = 'Data Entry Staff')),
('10000000-0000-0000-0000-000000000003', 'Grace T.', 'grace.t@alsj.example', '0772000003', '$2a$10$fMn/Zfqq88Ai2ElhJLfhe.rV8Dp4AA0H8xvx5r8NdSs4GhKZpzUEO', (SELECT role_id FROM roles WHERE role_name = 'Secretary')),
('10000000-0000-0000-0000-000000000004', 'Moses L.', 'moses.l@alsj.example', '0772000004', '$2a$10$fMn/Zfqq88Ai2ElhJLfhe.rV8Dp4AA0H8xvx5r8NdSs4GhKZpzUEO', (SELECT role_id FROM roles WHERE role_name = 'Director'))
ON CONFLICT DO NOTHING;

INSERT INTO staff_profiles (user_id, employee_no, date_hired) VALUES
('10000000-0000-0000-0000-000000000001', 'ALSJ-001', '2024-03-01'),
('10000000-0000-0000-0000-000000000002', 'ALSJ-002', '2024-06-15'),
('10000000-0000-0000-0000-000000000003', 'ALSJ-003', '2025-01-10'),
('10000000-0000-0000-0000-000000000004', 'ALSJ-004', '2023-09-01')
ON CONFLICT DO NOTHING;

-- 2. Audit Logs Rows[cite: 53]
INSERT INTO audit_logs (user_id, action, entity_type, entity_id, ip_address, created_at)
SELECT 
    '10000000-0000-0000-0000-000000000001'::UUID, 
    'DOCUMENT_VERIFIED', 
    'documents', 
    'Amina''s passport id', 
    '10.0.0.5'::INET, 
    '2026-10-06 09:30:00+03'::TIMESTAMPTZ
WHERE NOT EXISTS (
    SELECT 1 FROM audit_logs 
    WHERE action = 'DOCUMENT_VERIFIED' 
      AND entity_id = 'Amina''s passport id'
);

INSERT INTO audit_logs (user_id, action, entity_type, entity_id, ip_address, created_at)
SELECT 
    NULL, 
    'PAYMENT_COMPLETED', 
    'payments', 
    'Amina''s 50000 payment id', 
    NULL, 
    '2026-10-03 10:02:00+03'::TIMESTAMPTZ
WHERE NOT EXISTS (
    SELECT 1 FROM audit_logs 
    WHERE action = 'PAYMENT_COMPLETED' 
      AND entity_id = 'Amina''s 50000 payment id'
);

COMMIT;