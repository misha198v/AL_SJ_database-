# Run the fixed Django prototype

## 1. Install the integration SQL in pgAdmin

Use your existing administrator connection (postgres), select al_sj_database,
open Query Tool, and open sql/050_django_integration.sql from this backend folder.
Execute the whole file once. It is transactional and safe to run again.

Prerequisites: the team's 12 tables, 18 relationships, views, role grants and
previously tested routines must already exist. In particular, Data Entry needs
data_entry_decide_document(uuid,text,text) and
data_entry_change_stage(uuid,integer); Secretary needs secretary_save_appointment
and secretary_delete_appointment. The script adds restricted login/session
functions and a Field Agent stage wrapper. Install it as the trusted owner;
the web application never connects as that owner.

The SQL preserves the existing rows and password hashes. It requires pgcrypto
in public (as installed by the script). The application login receives EXECUTE
on authentication functions only, and no password_hash SELECT privilege.
Bcrypt 2a, 2b and 2y tags are accepted for passwords up to 72 UTF-8 bytes.

## 2. Set up the app in PowerShell

Open a terminal in this backend folder:

    python -m venv .venv
    .\.venv\Scripts\python.exe -m pip install -r requirements.txt
    Copy-Item .env.example .env

Open .env in VS Code and set DB_PASSWORD to the private password you previously
set for alsj_app_login in pgAdmin. DB_NAME should be al_sj_database.
The database-login password is separate from the users' website passwords.
Do not paste either password into chat or commit .env.

    .\.venv\Scripts\python.exe manage.py migrate --database=default
    .\.venv\Scripts\python.exe manage.py check
    .\.venv\Scripts\python.exe manage.py test core
    .\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8001

Open http://127.0.0.1:8001/login/ in your browser.

Django uses default SQLite for sessions and its own migration records.
The router blocks business-model writes and all PostgreSQL migrations. The
migrate command also rejects --database=alsj before Django's migration recorder
can create a table. Never run the seed files again to launch the UI.

## 3. Try your assigned part

Log in as Data Entry Staff using phone 0700000002 and that user's current
website password. Home opens Document queue. Open an application to verify or
reject a document or move it to a stage. A rejection requires a nonblank reason.
Time per stage opens the existing report; Download CSV exports its results.

Document decisions and stage changes are real database writes. Use a test clone
for experiments that should not change your shared demonstration data.

Other seeded phones: Director 0700000004, Secretary 0700000003, Field Agent
0700000001, clients 0772556213 / 0700000012 / 0700000013. Setup does not change their
passwords; Test1234! works only when it matches the stored bcrypt hashes.
Director is read-only. Secretary's menu intentionally exposes appointments only,
matching the currently installed grants. Other unsupported writes are disabled.

## 4. Verification

    .\.venv\Scripts\python.exe manage.py test core

This checks the SQLite/owner/migration/login boundaries without connecting to
PostgreSQL. test_integration.py is a separate destructive-fixture test for a
disposable database clone ONLY. It refuses to run unless ALSJ_INTEGRATION_TEST=1,
DB_NAME begins alsj_django_test_, and DB_PORT is 55439. It installs the new SQL
and changes fixture passwords/data in that clone. Never use it against the
existing project database.

An integration run with PostgreSQL 18 checked all five role logins, Director
pages, Data Entry queue/report/decisions/stages and their audit/history, Secretary
appointment creation/update/delete, cross-client/agent restrictions, CSRF, disabled
users, role revalidation and cleanup, no hash access, and 12 tables/18 foreign keys.

## Development and deployment notes

This is a local development prototype, not a deployment configuration.
For deployment set DJANGO_DEBUG=false, a private DJANGO_SECRET_KEY, HTTPS hosts,
and required TLS to PostgreSQL. Session cookies then require HTTPS. The bundled
per-process login attempt cache is suitable for this single-process local demo;
use a shared cache/rate limiter for a multi-worker deployment.

The backend is the trusted boundary. Only it may hold alsj_app_login credentials
and choose app.current_user_id from the authenticated server session. End users
must never receive that database password or a SQL console. The connection
identity is deliberately revalidated each request, including role/active changes.
The middleware uses one atomic(using='alsj') transaction, SET LOCAL ROLE from a
fixed allowlist, and set_config(...,true); request form fields cannot pick roles.

Django admin/auth endpoints and the bulk password-reset command are disabled.
The original inspectdb models remain unmanaged. ORM saves are blocked by the
router, and PostgreSQL denies direct table writes under application roles.
Do not bypass these boundaries with .using('alsj') writes or owner credentials.

The schema migration is additive and leaves no Django tables in PostgreSQL.
Reverting application code requires no data rollback. To revoke new access, the
DB owner can revoke EXECUTE on app_authenticate and app_session_identity from
alsj_app_login, and the new wrapper grants from their specific business roles.
Existing Data Entry/Secretary routines, triggers and constraints are unchanged.

No changes are committed, pushed or merged automatically.
