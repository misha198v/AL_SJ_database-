-- create_report_revenue_by_month_and_method.sql
-- Report: payments collected per month and payment method (and currency).
-- Source: PDF p.9 (payments: amount, currency, payment_method, status, completed_at),
--         p.4 (a refund keeps the original completion time)
-- Rule used for refunds: a REFUNDED payment was collected, so it counts in "collected" and is
-- subtracted in "net". Its month is the month of the ORIGINAL completion time.
-- PENDING and FAILED payments are not revenue and are left out.

CREATE OR REPLACE VIEW rpt_revenue_by_month_and_method AS
SELECT date_trunc('month', p.completed_at AT TIME ZONE 'Africa/Kampala')::date AS month,
       p.payment_method,
       p.currency,
       count(*)                                                          AS payments,
       sum(p.amount)                                                     AS collected_amount,
       COALESCE(sum(p.amount) FILTER (WHERE p.status = 'REFUNDED'), 0)   AS refunded_amount,
       COALESCE(sum(p.amount) FILTER (WHERE p.status = 'COMPLETED'), 0)  AS net_revenue
FROM payments p
WHERE p.status IN ('COMPLETED', 'REFUNDED')
GROUP BY 1, p.payment_method, p.currency
ORDER BY 1 DESC, p.payment_method;
