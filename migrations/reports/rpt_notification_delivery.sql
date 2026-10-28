-- =========================================================================
-- Description: Number of SENT, DELIVERED, and FAILED notifications per channel.
-- =========================================================================

CREATE OR REPLACE VIEW rpt_notification_delivery AS
SELECT 
    channel,
    SUM(CASE WHEN status = 'SENT' THEN 1 ELSE 0 END) AS sent_count,
    --SUM(CASE WHEN status = 'DELIVERED' THEN 1 ELSE 0 END) AS delivered_count,
    SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) AS failed_count,
    COUNT(*) AS total_notifications
FROM notifications
GROUP BY channel;