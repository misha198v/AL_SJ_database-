-- Task 3 report: one row per stage visit, based on the stage ENTERED (to_stage_id).
-- A visit ends at the next change for that application. Ongoing visits have NULL
-- duration and are excluded from the average. Repeated visits count separately.
-- changed_at/history_id provides deterministic ordering for equal timestamps.
CREATE OR REPLACE VIEW public.rpt_time_per_stage
WITH (security_invoker = true) AS
WITH visits AS (
    SELECT sh.history_id, sh.application_id, sh.to_stage_id AS stage_id,
           sh.changed_at AS entered_at,
           lead(sh.changed_at) OVER (
               PARTITION BY sh.application_id ORDER BY sh.changed_at, sh.history_id
           ) AS exited_at
    FROM public.stage_history AS sh
), durations AS (
    SELECT visits.*, exited_at - entered_at AS time_in_stage FROM visits
)
SELECT d.history_id, d.application_id, d.stage_id, s.stage_order, s.stage_name,
       d.entered_at, d.exited_at, d.time_in_stage,
       avg(d.time_in_stage) OVER (PARTITION BY d.stage_id) AS average_time_in_stage,
       count(d.time_in_stage) OVER (PARTITION BY d.stage_id) AS completed_visit_count
FROM durations AS d
JOIN public.pipeline_stages AS s ON s.stage_id = d.stage_id
ORDER BY d.application_id, d.entered_at, d.history_id;
