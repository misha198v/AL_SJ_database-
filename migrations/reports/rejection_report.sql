-- 02_rpt_document_rejection_rate.sql
-- REPORT (saved as a view): per document type -> total documents,
-- number REJECTED, rejection percentage, and the rejection reasons.
-- Safe to re-run: CREATE OR REPLACE VIEW.

CREATE OR REPLACE VIEW rpt_document_rejection_rate AS
SELECT
    d.document_type,
    COUNT(*)                                          AS total_documents,
    COUNT(*) FILTER (WHERE d.verification_status = 'REJECTED')     AS rejected_documents,
    -- 100.0 forces decimal division (100 / 3 would be integer division)
    ROUND(100.0 * COUNT(*) FILTER (WHERE d.verification_status = 'REJECTED')
                / COUNT(*), 1)                        AS rejection_percentage,
    -- All distinct reasons joined into one text; NULL when none rejected
    STRING_AGG(DISTINCT d.rejection_reason, '; ')
        FILTER (WHERE d.verification_status = 'REJECTED')          AS rejection_reasons
FROM documents d
GROUP BY d.document_type
ORDER BY d.document_type;

-- Check it:
-- SELECT * FROM rpt_document_rejection_rate;
-- Expected on the full seed:
--   NATIONAL_ID        1 total, 0 rejected,   0.0 %, NULL
--   PASSPORT           1 total, 0 rejected,   0.0 %, NULL
--   TRAVEL_DECLARATION 1 total, 1 rejected, 100.0 %, Signature missing on page 2