-- =========================================================================
-- Seed File: seed_notifications.sql
-- Description: Seeds roles, stages, staff, client parent records, 
--              and the 3 system notifications.
-- Source: SEEDING POLL.pdf p. 2 & seed_base_block.sql[cite: 51, 54]
-- =========================================================================

BEGIN;

-- 1. Base Block (Roles, Stages, Staff Users & Staff Profiles)
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

-- 2. Parent Records (Amina and Cathy)[cite: 51]
INSERT INTO users (user_id, full_name, email, phone, password_hash, role_id) VALUES
('10000000-0000-0000-0000-000000000011', 'Amina N.', NULL, '0772556213', '$2a$10$fMn/Zfqq88Ai2ElhJLfhe.rV8Dp4AA0H8xvx5r8NdSs4GhKZpzUEO', (SELECT role_id FROM roles WHERE role_name = 'Client')),
('10000000-0000-0000-0000-000000000012', 'Cathy M.', NULL, '0700000012', '$2a$10$fMn/Zfqq88Ai2ElhJLfhe.rV8Dp4AA0H8xvx5r8NdSs4GhKZpzUEO', (SELECT role_id FROM roles WHERE role_name = 'Client'))
ON CONFLICT DO NOTHING;

INSERT INTO client_profiles (user_id, national_id, date_of_birth, address, preferred_language) VALUES
('10000000-0000-0000-0000-000000000011', 'CM88213456', '1994-05-12', 'Jinja Road, Kampala', 'EN'),
('10000000-0000-0000-0000-000000000012', 'CF90112233', '1996-08-03', 'Entebbe', 'EN')
ON CONFLICT DO NOTHING;

INSERT INTO applications (application_id, client_id, assigned_agent_id, current_stage_id, service_type, destination, travel_purpose, preferred_travel_date, status) VALUES
('20000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000011', '10000000-0000-0000-0000-000000000001', (SELECT stage_id FROM pipeline_stages WHERE stage_order = 1), 'DOMESTIC_TOURISM', 'Jinja', 'Family holiday', '2026-12-12', 'ACTIVE'),
('20000000-0000-0000-0000-000000000002', '10000000-0000-0000-0000-000000000002', NULL, (SELECT stage_id FROM pipeline_stages WHERE stage_order = 1), 'LABOUR_MIGRATION', 'Dubai', 'Hospitality work', '2027-01-20', 'ACTIVE')
ON CONFLICT DO NOTHING;

-- 3. Notifications Rows
INSERT INTO notifications (user_id, application_id, channel, message, status)
SELECT 
    '10000000-0000-0000-0000-000000000011'::UUID, 
    '20000000-0000-0000-0000-000000000001'::UUID, 
    'SMS'::notification_channel_enum, 
    'Your passport has been verified.', 
    'DELIVERED'::notification_status_enum
WHERE NOT EXISTS (
    SELECT 1 FROM notifications 
    WHERE user_id = '10000000-0000-0000-0000-000000000011' 
      AND message = 'Your passport has been verified.'
);

INSERT INTO notifications (user_id, application_id, channel, message, status)
SELECT 
    '10000000-0000-0000-0000-000000000012'::UUID, 
    '20000000-0000-0000-0000-000000000002'::UUID, 
    'SMS'::notification_channel_enum, 
    'We could not process your payment. Please try again.', 
    'FAILED'::notification_status_enum
WHERE NOT EXISTS (
    SELECT 1 FROM notifications 
    WHERE user_id = '10000000-0000-0000-0000-000000000012' 
      AND message = 'We could not process your payment. Please try again.'
);

INSERT INTO notifications (user_id, application_id, channel, message, status)
SELECT 
    '10000000-0000-0000-0000-000000000001'::UUID, 
    NULL, 
    'EMAIL'::notification_channel_enum, 
    'Daily summary: 2 applications need attention.', 
    'SENT'::notification_status_enum
WHERE NOT EXISTS (
    SELECT 1 FROM notifications 
    WHERE user_id = '10000000-0000-0000-0000-000000000001' 
      AND message = 'Daily summary: 2 applications need attention.'
);

COMMIT;