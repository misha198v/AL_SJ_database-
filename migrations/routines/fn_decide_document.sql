-- fn_decide_document.sql
-- Verify or reject a PENDING document. Django calls this instead of .save()/.update().
-- The audit row is written automatically by trg_documents_decision_audit.

CREATE OR REPLACE FUNCTION fn_decide_document(
    p_document_id      UUID,
    p_decision         TEXT,      -- 'VERIFIED' or 'REJECTED'
    p_reviewer_id      UUID,
    p_rejection_reason TEXT DEFAULT NULL
) RETURNS VOID AS $$
BEGIN
    IF p_decision NOT IN ('VERIFIED', 'REJECTED') THEN
        RAISE EXCEPTION 'Decision must be VERIFIED or REJECTED, got %', p_decision;
    END IF;

    IF p_decision = 'REJECTED' AND (p_rejection_reason IS NULL OR trim(p_rejection_reason) = '') THEN
        RAISE EXCEPTION 'A rejection reason is required.';
    END IF;

    UPDATE documents
    SET verification_status = p_decision::verification_status_enum,
        verified_by         = p_reviewer_id,
        verified_at         = now(),
        rejection_reason    = CASE WHEN p_decision = 'REJECTED'
                                   THEN trim(p_rejection_reason) ELSE NULL END
    WHERE document_id = p_document_id
      AND verification_status = 'PENDING';

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Document % not found or already decided.', p_document_id;
    END IF;
END;
$$ LANGUAGE plpgsql;