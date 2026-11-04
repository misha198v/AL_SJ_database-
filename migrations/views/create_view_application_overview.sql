-- create_view_application_overview.sql
-- View: one row per application with client, agent, stage, service, destination and status.
-- Source: PDF p.3 (clients track application progress), p.5 (users), p.6 (pipeline_stages),
--         p.7 (applications)
-- security_invoker = the view uses the permissions (and row-level security) of whoever reads it.
-- That needs PostgreSQL 15 or newer.

DO $$
BEGIN
    IF current_setting('server_version_num')::int < 150000 THEN
        RAISE EXCEPTION 'v_application_overview needs PostgreSQL 15 or newer (run SELECT version();)';
    END IF;
END $$;

CREATE OR REPLACE VIEW v_application_overview
WITH (security_invoker = true) AS
SELECT a.application_id,
       a.client_id,
       c.full_name            AS client_name,
       c.phone                AS client_phone,
       ag.full_name           AS agent_name,        -- empty when no agent is assigned yet
       ps.stage_order,
       ps.stage_name,
       a.service_type,
       a.destination,
       a.preferred_travel_date,
       a.status,
       a.created_at
FROM applications a
JOIN users c            ON c.user_id   = a.client_id
JOIN pipeline_stages ps ON ps.stage_id = a.current_stage_id
LEFT JOIN users ag      ON ag.user_id  = a.assigned_agent_id;
