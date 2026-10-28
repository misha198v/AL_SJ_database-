-- Task 3 view: pending documents, oldest first. PostgreSQL 15+.
-- Invoker security respects the calling role's grants and row-level policies.
CREATE OR REPLACE VIEW public.v_document_review_queue
WITH (security_invoker = true) AS
SELECT d.document_id, d.application_id, u.full_name AS client_name,
       d.document_type, d.uploaded_at, a.destination
FROM public.documents AS d
JOIN public.applications AS a ON a.application_id = d.application_id
JOIN public.users AS u ON u.user_id = a.client_id
WHERE d.verification_status = 'PENDING'
ORDER BY d.uploaded_at, d.document_id;
