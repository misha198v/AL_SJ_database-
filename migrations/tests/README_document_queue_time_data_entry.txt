TASK 3 ONLY: Document queue + Time-per-stage + Data Entry Staff database role

Apply these files in order in the SAME project database, as a trusted owner:
1. migrations/views/v_document_review_queue.sql
2. migrations/reports/rpt_time_per_stage.sql
3. migrations/routines/data_entry_decide_document.sql
4. migrations/routines/data_entry_change_stage.sql
5. migrations/roles/create_role_data_entry_staff.sql

Prerequisites: PostgreSQL 15+; project tables; the existing
change_stage(UUID, INTEGER, UUID) function; document checks and decision audit trigger.
Install migrations/triggers/043_create_function_change_stage.sql if the routine
is missing, but do not recreate it if already installed. No table, column or
relationship changes are made by the five Task 3 files. All are safe to rerun.
One file per object. The two extra routines support the role's allowed actions:
the existing triggers lock/read protected users and insert audit rows, so direct
UPDATE grants alone would require extra user/audit privileges. The narrow routines
execute those operations as their trusted owner and do not expose password data.
Do not install the routines as an application/login user or untrusted table owner.
They use a fixed search_path and qualified names, and PUBLIC cannot execute them.

Then run these WHOLE files in pgAdmin as owner:
- migrations/tests/test_document_queue_time_per_stage.sql
- migrations/tests/test_data_entry_staff_role.sql
They report PASS notices, test allowed and refused actions with SET ROLE, and
roll back their fixture updates/audit entries. If a test stops with an error,
run ROLLBACK; before continuing. Tests may advance sequence counters.

Expected seeded results (hand counts):
- Queue: one pending document, Amina's national ID.
- Report: six stage visits. Three completed visits and three ongoing visits.
- Amina Registered: 25 hours; Docs Pending: 73 hours.
- Daniel Registered: 25 hours. Cathy Registered is ongoing.
- Average Registered: 25 hours across two completed visits.
- Average Docs Pending: 73 hours across one completed visit.
Current visits have NULL end/duration and do not contribute to AVG. These are
elapsed times, not business hours. A revisit is another observation. Ties in
changed_at use history_id. Ordering consumers can specify ORDER BY explicitly.

Role usage example, after an administrator grants membership to the app login:
GRANT alsj_data_entry_staff TO app_user WITH INHERIT FALSE;
BEGIN;
SET LOCAL ROLE alsj_data_entry_staff;
SET LOCAL app.current_user_id = '10000000-0000-0000-0000-000000000002';
SELECT * FROM public.v_document_review_queue;
SELECT public.data_entry_decide_document('<document uuid>', 'VERIFIED', NULL);
SELECT public.data_entry_change_stage('<application uuid>', <stage_id>);
COMMIT;
The membership example uses PostgreSQL 16+ syntax (the project uses 18).
PostgreSQL 15 administrators should use their login role's NOINHERIT membership setup.
The backend MUST set app.current_user_id from the authenticated session, not from
an arbitrary client-supplied value. The role does not authenticate end-user identities.
It is a NOLOGIN group, separate from the row named Data Entry Staff in public.roles.
The routines require an active Data Entry Staff actor. The document routine takes
VERIFIED or REJECTED (with a nonblank reason); the existing triggers/checks still run.
The stage routine delegates to the team's existing change_stage function.
The role has no direct document/application UPDATE or audit INSERT rights.

Password handling:
The role grants SELECT on named safe users columns, never password_hash.
Role installation refuses to commit if PUBLIC/inherited rights expose password_hash.
SELECT * FROM users is also refused; select safe columns explicitly.
Role-specific SELECT policies allow work when the Client file has enabled RLS.
Invoker-security views respect the caller's table grants and policies.
The separate application login file currently grants broad SELECT on users;
that separate role's permissions are NOT changed here. Use SET ROLE for this task.
An administrator must review the full application's permissions before deployment.

Validation and current team-data limitations:
- Tested on an isolated PostgreSQL 18 database with Client RLS, document-verifier,
  document audit, history protection, initial-history and profile-rule triggers.
- Seed fixtures match three client stories, six history rows, three documents.
- The repository currently supplies 44/49 seed records; the notification/audit seed
  (five rows) is absent and is unrelated to these view/report hand counts.
- The test fixture alone allowed stage_history.from_stage_id to be NULL, as the
  seed specification requires. The repository table still declares NOT NULL.
- Daniel's identity seed references created_at instead of changed_at and assumes
  an initial-history trigger exists before disabling it. Only the isolated test
  copy was corrected for these prerequisite errors. Teammates' files were not edited.
- Full unmodified-project setup is therefore not claimed as passing.

No Git commits, pushes, pull requests or real pgAdmin database changes were made.
The assignment requests a separate pull request per file, reviewed by a teammate.
