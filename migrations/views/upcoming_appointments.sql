CREATE OR REPLACE VIEW v_upcoming_appointments AS
SELECT 
    s.schedule_id AS appointment_id,
    u_staff.full_name AS staff_member,
    u_client.full_name AS client_name,
    s.appointment_type,
    s.scheduled_datetim AS appointment_datetime -- update column name if full word is visible in your schema
FROM schedule_records s
JOIN users u_staff ON s.staff_id = u_staff.user_id
JOIN users u_client ON s.client_id = u_client.user_id
WHERE s.status = 'UPCOMING'
ORDER BY s.scheduled_datetime ASC;