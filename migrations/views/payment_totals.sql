-- 01_v_application_payment_totals.sql
-- VIEW: per application, total amount and number of COMPLETED payments.
-- Supports the deposit rule (PDF p.4 and p.9).
-- Safe to re-run: CREATE OR REPLACE VIEW.
-- Column names follow the group data dictionary (design PDF, Section 02).

CREATE OR REPLACE VIEW v_application_payment_totals AS
SELECT
    a.application_id,
    -- COALESCE turns "no completed payments" (NULL) into 0
    COALESCE(SUM(p.amount), 0)  AS total_completed_amount,
    COUNT(p.payment_id)         AS completed_payment_count
FROM applications a
-- LEFT JOIN keeps applications that have no completed payment.
-- The status test sits in the JOIN condition (not WHERE) so those
-- applications are not filtered out.
LEFT JOIN payments p
       ON p.application_id = a.application_id
      AND p.status = 'COMPLETED'
GROUP BY a.application_id;

-- Check it:
-- SELECT * FROM v_application_payment_totals ORDER BY application_id;
-- Expected on the full 49-record seed:
--   ...0001 (Amina) -> 50000, 1   (the 20000 payment is PENDING)
--   ...0002 (Cathy) ->     0, 0   (her payment FAILED)
--   ...0003 (Daniel)->     0, 0   (his payment is REFUNDED)