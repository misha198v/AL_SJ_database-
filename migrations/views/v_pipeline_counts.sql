-- v_pipeline_counts.sql
-- Number of applications per pipeline stage and per service type.
-- All seven stages appear, even with zero applications.

CREATE OR REPLACE VIEW v_pipeline_counts AS
SELECT
    ps.stage_order,
    ps.stage_name,
    st.service_type,
    COUNT(a.application_id) AS application_count
FROM pipeline_stages ps
CROSS JOIN (
    SELECT DISTINCT service_type FROM applications
) st
LEFT JOIN applications a
       ON a.current_stage_id = ps.stage_id
      AND a.service_type = st.service_type
GROUP BY ps.stage_order, ps.stage_name, st.service_type
ORDER BY ps.stage_order, st.service_type;