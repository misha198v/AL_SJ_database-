CREATE OR REPLACE VIEW rpt_payment_follow_up AS
SELECT 
    p.payment_id,
    p.status AS payment_status,
    u.full_name AS client_name,
    app.destination,
    p.payer_phone,
    p.amount,
    p.initiated_at AS start_time
FROM payments p
JOIN applications app ON p.application_id = app.application_id
JOIN users u ON app.client_id = u.user_id
WHERE p.status IN ('PENDING', 'FAILED');
