-- v_document_review_queue.sql
-- Every PENDING document with client name, document type,
-- upload time and destination, oldest first (PDF p.8).

CREATE OR REPLACE VIEW v_document_review_queue AS
SELECT
    d.document_id,
    d.application_id,
    u.full_name  AS client_name,
    d.document_type,
    d.uploaded_at,
    a.destination
FROM documents d
JOIN applications a ON a.application_id = d.application_id
JOIN users u        ON u.user_id = a.client_id
WHERE d.verification_status = 'PENDING'
ORDER BY d.uploaded_at ASC;